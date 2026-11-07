#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_video.py — 按分集表把整片切成每集视频

产出（两个文件夹）：
  <out-burned>/NN.mp4        字幕烧录进画面
  <out-clean>/NN.mp4         无字幕画面
  <out-clean>/NN.mp4.srt     该集独立字幕（从 0 起算）

典型用法：
  # 1) 先拆字幕（产出每集 srt）
  python split_srt.py --srt master.srt --csv episodes.xlsx --out srt_out

  # 2) 再切视频（读上一步的 srt_out）
  python split_video.py --video "整片.mp4" --table episodes.xlsx --srt-dir srt_out \
      --out-burned burned --out-clean clean_srt

常用可选项：
  --episodes 1-3          只处理指定集（也可 1,5,9）；不填=全部
  --fps 24                帧率（默认读 xlsx 的 G1，仍无则 25）
  --ref "某集.mp4"         参考你已有的一集导出，自动抄它的分辨率/码率规格
  --width 2520 --height 1080   直接指定输出分辨率（不填=源分辨率）
  --encoder h264_nvenc    编码器（默认自动探测 NVENC，没有则 libx264）
  --cq 16                 质量（NVENC 用 cq / x264 用 crf）

  # 想让字幕大小/位置精确对齐你已在用的样式（像素级）：
  --sub-size 43 --sub-margin-v 44 --sub-outline 2 --sub-font Arial

  --dry-run               只打印计划，不动文件
"""

import os
import re
import sys
import glob
import time
import shutil
import argparse
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from split_srt import parse_tc, cell_to_ms, read_table, read_fps_from_xlsx, fmt_tc  # noqa: E402


# ---------------- ffmpeg / ffprobe 定位 ----------------
def _probe_candidates():
    here = os.path.dirname(os.path.abspath(__file__))
    return [
        os.environ.get('FFMPEG'),
        shutil.which('ffmpeg'),
        os.path.join(here, '..', 'ffmpeg', 'bin', 'ffmpeg.exe'),
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'D:\ffmpeg\bin\ffmpeg.exe',
        r'E:\ffmpeg\bin\ffmpeg.exe',
        r'F:\ffmpeg\bin\ffmpeg.exe',
    ]


def find_tools():
    ff = None
    for c in _probe_candidates():
        if c and os.path.exists(c):
            ff = c
            break
    if not ff:
        # 兜底：在各用户目录下找 ffmpeg-*/bin/ffmpeg.exe
        for pat in (r'C:\Users\*\ffmpeg\**\bin\ffmpeg.exe',):
            hits = glob.glob(pat, recursive=True)
            if hits:
                ff = hits[0]
                break
    if not ff:
        sys.exit('✗ 找不到 ffmpeg。请把 ffmpeg.exe / ffprobe.exe 加入 PATH，'
                 '或设置环境变量 FFMPEG 指向 ffmpeg 可执行文件')
    fp = os.path.join(os.path.dirname(ff), 'ffprobe.exe')
    if not os.path.exists(fp):
        fp = shutil.which('ffprobe') or fp
    return ff, fp


FFMPEG, FFPROBE = find_tools()


def run(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if check and r.returncode != 0:
        raise RuntimeError('ffmpeg failed (%d):\n%s\n%s' % (r.returncode, cmd, r.stderr[-1500:]))
    return r


def ffprobe_json(args):
    r = run([FFPROBE, '-v', 'error', '-of', 'json'] + args)
    import json
    return json.loads(r.stdout or '{}')


def probe_video(path):
    d = ffprobe_json(['-show_entries', 'stream=width,height,r_frame_rate,codec_name',
                      '-select_streams', 'v:0', '-show_entries', 'format=duration', path])
    st = (d.get('streams') or [{}])[0]
    fps = 0.0
    rfr = st.get('r_frame_rate', '0/1')
    try:
        a, b = rfr.split('/')
        fps = float(a) / float(b) if float(b) else 0.0
    except Exception:
        pass
    return {
        'width': st.get('width'), 'height': st.get('height'),
        'fps': fps, 'vcodec': st.get('codec_name'),
        'duration': float(d.get('format', {}).get('duration') or 0),
    }


def probe_bitrate(path):
    d = ffprobe_json(['-show_entries', 'format=bit_rate', path])
    try:
        return int(d.get('format', {}).get('bit_rate') or 0)
    except Exception:
        return 0


def has_encoder(name):
    out = run([FFMPEG, '-hide_banner', '-encoders'], check=False).stdout
    return any(re.search(r'\b%s\b' % re.escape(name), l) for l in out.splitlines())


_PROBE_CACHE = {}


def probe_encoder(name, w=640, h=360):
    """实测编码器能否真正初始化。

    ffmpeg -encoders 列出的是**编译进来的**编码器，不代表本机能跑：
    例如 h264_nvenc 在没有 NVIDIA 卡、或驱动 NVENC API 版本低于 ffmpeg 编译
    所用 SDK 时会直接报错（"Driver does not support the required nvenc API"）。
    只查列表会导致自动选中一个跑不起来的编码器。
    """
    if name in _PROBE_CACHE:
        return _PROBE_CACHE[name]
    r = run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error',
             '-f', 'lavfi', '-i', 'testsrc=size=%dx%d:rate=30' % (w, h),
             '-t', '1', '-c:v', name, '-f', 'null', '-'], check=False)
    ok = (r.returncode == 0 and not (r.stderr or '').strip())
    _PROBE_CACHE[name] = ok
    if not ok:
        _PROBE_CACHE[name + ':why'] = ((r.stderr or '').strip().splitlines() or ['unknown'])[0][:120]
    return ok


def _probe_reason(name):
    return _PROBE_CACHE.get(name + ':why', '未知原因')


# ---------------- 字幕样式（像素级精控） ----------------
def srt_to_styled_ass(srt_src, work_dir, name, play_w, play_h, font, size,
                      margin_v, outline, bold=0):
    """把 SRT 转成 ASS，并把 PlayRes 设成输出分辨率 —— 此时 Fontsize/MarginV 就是像素值。"""
    ass = os.path.join(work_dir, name)
    run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'error',
         '-i', os.path.basename(srt_src), os.path.basename(ass)], cwd=work_dir)
    txt = open(ass, encoding='utf-8').read()
    txt = re.sub(r'PlayResX:\s*\d+', 'PlayResX: %d' % play_w, txt, count=1)
    txt = re.sub(r'PlayResY:\s*\d+', 'PlayResY: %d' % play_h, txt, count=1)
    style = ('Style: Default,%s,%d,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,'
             '%d,0,0,0,100,100,0,0,1,%d,0,2,10,10,%d,1'
             % (font, size, bold, outline, margin_v))
    txt = re.sub(r'Style: Default,[^\n]*', style, txt, count=1)
    open(ass, 'w', encoding='utf-8').write(txt)
    return ass  # 已在 work_dir 内，burn 时只需 basename


# ---------------- 主流程 ----------------
def main():
    ap = argparse.ArgumentParser(description='按分集表把整片切成每集视频')
    ap.add_argument('--video', required=True, help='整片源视频')
    ap.add_argument('--table', required=True, help='分集表 .xlsx/.csv（A=集号 B=start C=end）')
    ap.add_argument('--srt-dir', required=True, help='每集 SRT 目录（split_srt.py 的 --out）')
    ap.add_argument('--out-burned', default='burned', help='烧录字幕版输出目录')
    ap.add_argument('--out-clean', default='clean_srt', help='无字幕版+独立字幕输出目录')
    ap.add_argument('--episodes', default='', help='只处理指定集，如 1-3 / 1,5,9')
    ap.add_argument('--name-format', default='{ep:02d}.mp4',
                    help='输出命名模板，用 {ep} 占位，如 "女巫与狼王ep{ep:03d}.mp4"；'
                         '独立字幕版会追加同名 .srt')
    ap.add_argument('--fps', type=float, default=None, help='帧率（默认读 xlsx G1）')
    ap.add_argument('--ref', default='', help='参考已有导出，自动抄分辨率/码率')
    ap.add_argument('--width', type=int, default=0)
    ap.add_argument('--height', type=int, default=0)
    ap.add_argument('--bitrate', default='', help='目标码率，如 12M（不填=按 ref 或 12M）')
    ap.add_argument('--encoder', default='', help='视频编码器（默认自动）')
    ap.add_argument('--cq', type=int, default=16, help='质量：NVENC cq / x264 crf（越小越好）')
    ap.add_argument('--preset', default='', help='编码 preset（默认 NVENC p6 / x264 medium）')
    ap.add_argument('--audio-bitrate', default='192k')
    ap.add_argument('--sub-font', default='', help='字幕字体（不填=libass 默认 Arial）')
    ap.add_argument('--sub-size', type=int, default=0, help='字幕字号（像素；需配合 --sub-margin-v）')
    ap.add_argument('--sub-margin-v', type=int, default=0, help='字幕距底像素')
    ap.add_argument('--sub-outline', type=int, default=0, help='描边像素（默认 0=用默认样式）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    # [修复] 本脚本会把 ffmpeg 的 cwd 切到一个纯 ASCII 临时目录（见下方 work，
    # 目的是绕开 subtitles 滤镜对中文/冒号路径的限制）。因此**所有传给 ffmpeg 的
    # 路径必须绝对化**，否则相对路径在临时目录下必然 "No such file or directory"。
    args.video      = os.path.abspath(args.video)
    args.table      = os.path.abspath(args.table)
    args.srt_dir    = os.path.abspath(args.srt_dir)
    args.out_burned = os.path.abspath(args.out_burned)
    args.out_clean  = os.path.abspath(args.out_clean)
    if args.ref:
        args.ref = os.path.abspath(args.ref)

    if not os.path.exists(args.video):
        sys.exit('✗ 找不到视频：%s' % args.video)
    if not os.path.exists(args.table):
        sys.exit('✗ 找不到分集表：%s' % args.table)
    if not os.path.isdir(args.srt_dir):
        sys.exit('✗ 找不到每集字幕目录：%s（先跑 split_srt.py）' % args.srt_dir)

    # ---- 规格：优先 --ref，其次 --width/--height，否则源分辨率 ----
    src = probe_video(args.video)
    ref_spec = None
    if args.ref:
        if not os.path.exists(args.ref):
            sys.exit('✗ --ref 文件不存在：%s' % args.ref)
        ref_spec = probe_video(args.ref)
        ref_br = probe_bitrate(args.ref)
        print('参考规格: %sx%s @%s  %.2f Mbps'
              % (ref_spec['width'], ref_spec['height'], ref_spec['fps'], ref_br / 1e6))
    out_w = args.width or (ref_spec['width'] if ref_spec else src['width'])
    out_h = args.height or (ref_spec['height'] if ref_spec else src['height'])
    bitrate = args.bitrate or ('%.2fM' % (probe_bitrate(args.ref) / 1e6) if args.ref else '12M')

    # ---- 编码器 ----
    enc = args.encoder
    if not enc:
        enc = None
        for cand in ('h264_nvenc', 'h264_qsv', 'h264_amf'):
            if has_encoder(cand):
                if probe_encoder(cand):
                    enc = cand
                    break
                print('  提示：%s 在列表中但实测不可用，跳过（%s）'
                      % (cand, _probe_reason(cand)))
        if not enc:
            enc = 'libx264'
            print('  提示：无可用硬件编码器，回落 CPU libx264')
    if any(k in enc for k in ('nvenc',)):
        preset = args.preset or 'p6'
        venc = ['-c:v', enc, '-preset', preset, '-tune', 'hq', '-rc', 'vbr',
                '-cq', str(args.cq), '-b:v', bitrate,
                '-maxrate', '20M', '-bufsize', '40M', '-pix_fmt', 'yuv420p']
    else:
        preset = args.preset or 'medium'
        venc = ['-c:v', enc, '-preset', preset, '-crf', str(args.cq),
                '-b:v', bitrate, '-maxrate', '20M', '-bufsize', '40M', '-pix_fmt', 'yuv420p']
    aenc = ['-c:a', 'aac', '-b:a', args.audio_bitrate, '-movflags', '+faststart']

    # ---- 帧率 ----
    fps = args.fps
    if fps is None and args.table.lower().endswith('.xlsx'):
        fps = read_fps_from_xlsx(args.table)
    fps = fps or (src['fps'] or 25.0)
    print('源视频: %sx%s  %.1ffps  时长 %.1fs' % (src['width'], src['height'], src['fps'], src['duration']))
    print('输出:   %sx%s  %s  cq=%d  码率≈%s' % (out_w, out_h, enc, args.cq, bitrate))
    print('帧率(用于解析时间码) = %s' % fps)

    # ---- 字幕样式（像素级；PlayRes 设成输出分辨率，故字号/距底就是像素）----
    styled = bool(args.sub_size or args.sub_margin_v or args.sub_font or args.sub_outline)
    if styled:
        # 未给的值按输出高度等比兜底（1080p 实测标定：Fontsize 52 → 可见字形高 43px）
        k = out_h / 1080.0
        sub_size = args.sub_size or max(8, round(52 * k))
        sub_mv = args.sub_margin_v or max(8, round(44 * k))
        sub_ol = args.sub_outline or max(1, round(2 * k))
        print('字幕样式: %s 字号 %dpx  距底 %dpx  描边 %dpx'
              % (args.sub_font or 'Arial', sub_size, sub_mv, sub_ol))
    else:
        sub_size = sub_mv = sub_ol = 0
        print('字幕样式: libass 默认（Arial，1080p 下字形高约 50px）')

    # ---- 选集 ----
    want = set()
    for a in args.episodes.split(','):
        a = a.strip()
        if not a:
            continue
        if '-' in a:
            lo, hi = a.split('-')
            want.update(range(int(lo), int(hi) + 1))
        else:
            want.add(int(a))

    rows = []
    for ep_raw, st_raw, en_raw in read_table(args.table):
        ep = str(ep_raw).strip() if ep_raw is not None else ''
        st = str(st_raw).strip() if st_raw is not None else ''
        en = str(en_raw).strip() if en_raw is not None else ''
        if not (ep and st and en):
            continue
        if re.search(r'[A-Za-z]', st) or re.search(r'[A-Za-z]', en):
            continue
        try:
            epn = int(ep)
            s0 = cell_to_ms(st_raw, fps)
            e0 = cell_to_ms(en_raw, fps)
        except Exception:
            continue
        if s0 is None or e0 is None or e0 <= s0:
            continue
        if want and epn not in want:
            continue
        rows.append((epn, s0, e0))

    if not rows:
        sys.exit('✗ 分集表里没有可处理的行（检查 start/end 是否已填）')

    print('\n共 %d 集待处理：' % len(rows))
    for epn, s0, e0 in rows:
        print('  EP%02d  %s -> %s  时长 %s'
              % (epn, fmt_tc(s0).replace(',', '.'), fmt_tc(e0).replace(',', '.'),
                 fmt_tc(e0 - s0)))
    if args.dry_run:
        print('\n[dry-run] 未执行。')
        return

    os.makedirs(args.out_burned, exist_ok=True)
    os.makedirs(args.out_clean, exist_ok=True)
    # 字幕滤镜不接受中文/冒号路径 → 统一放 ASCII 临时目录，并把 cwd 设为它
    work = tempfile.mkdtemp(prefix='subsplit_', dir=tempfile.gettempdir())

    scale = ''
    if (out_w, out_h) != (src['width'], src['height']):
        scale = 'scale=%d:%d:flags=lanczos' % (out_w, out_h)

    t0 = time.time()
    for epn, s0, e0 in rows:
        srt_src = os.path.join(args.srt_dir, 'episode_%02d.srt' % epn)
        if not os.path.exists(srt_src):
            print('  [跳过] EP%02d：找不到 %s' % (epn, srt_src))
            continue
        local = os.path.join(work, 'ep%02d.srt' % epn)
        shutil.copy(srt_src, local)
        if styled:
            srt_to_styled_ass(local, work, 'ep%02d.ass' % epn, out_w, out_h,
                              args.sub_font or 'Arial', sub_size, sub_mv, sub_ol)
            sub_file = 'ep%02d.ass' % epn
        else:
            sub_file = os.path.basename(local)

        dur = (e0 - s0) / 1000.0
        try:
            ep_name = args.name_format.format(ep=epn)
        except Exception:
            ep_name = '%02d.mp4' % epn
        base_in = ['-ss', '%.3f' % (s0 / 1000.0), '-i', args.video, '-t', '%.3f' % dur]
        vf_burn = ','.join(p for p in (scale, 'subtitles=%s' % sub_file) if p)
        vf_clean = scale or 'null'

        out_b = os.path.join(args.out_burned, ep_name)
        out_c = os.path.join(args.out_clean, ep_name)
        out_s = out_c + '.srt'

        tb = time.time()
        run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'warning'] + base_in +
            ['-vf', vf_burn] + venc + aenc + [out_b], cwd=work)
        t_burn = time.time() - tb
        tb = time.time()
        run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'warning'] + base_in +
            ['-vf', vf_clean] + venc + aenc + [out_c], cwd=work)
        t_clean = time.time() - tb
        shutil.copy(srt_src, out_s)

        print('  [EP%02d] dur=%.1fs burn=%.1fs clean=%.1fs -> %s / %s + srt'
              % (epn, dur, t_burn, t_clean, ep_name, ep_name), flush=True)

    shutil.rmtree(work, ignore_errors=True)
    print('\n全部完成，用时 %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
