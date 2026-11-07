# Sources and Further Reading

This project contains original operational rules synthesized from practical testing, public technical sources, open-source projects, and established film-language concepts. It does not reproduce books, films, private prompt canvases, or proprietary datasets.

> **Wan3.0 adaptation.** `director-wan3-prompt` adapts the `director-seedance-prompt` skill to Wan3.0 (`wan3.0-video`). The film-language methodology and the research/open-source provenance below are retained from that skill, and the Seedance links document the original research base. Wan3.0 model semantics (single `wan3.0-video` model, `Tmax=30s`, `<=5000` characters, native `@图片N/@视频N/@音频N` handles) supersede the Seedance version notes (2.0/2.5, 15s/30s, item ceilings) wherever they conflict.

## Research and Open Source

- [ByteDance Seed: Seedance 2.0 official launch](https://seed.bytedance.com/blog/seedance-2-0-official-launch) - official confirmation of multimodal reference input and up to 15-second high-quality output; checked 2026-07-31.
- [Volcengine Developer Community: Seedance 2.5 overview](https://developer.volcengine.com/articles/7662296461874298886) - community/partner article reporting a 30-second standard mode and up to 50 input items; checked 2026-07-31. Because this is not a ByteDance Seed product-spec page, the Skill treats these as a user-selected workflow profile and conditions the 50-item ceiling on the active product entry actually supporting it.
- [CineTechBench](https://github.com/pris-cv/cinetechbench) - cinematography dimensions for video understanding.
- [Intelligent Cinematography: A Systematic Review](https://link.springer.com/article/10.1007/s10462-024-11089-3) - shot planning and camera-control taxonomy.
- [OpenTimelineIO](https://opentimelineio.readthedocs.io/en/latest/) - editorial timeline, clip, transition, marker, and metadata concepts.
- [Language of Film Key Terms](https://pzacad.pitzer.edu/~mma/teaching/MS50/MS50_keyterms.html) - continuity, axis, POV, reaction, eyeline, and match-on-action terminology.
- [ACES Documentation](https://docs.acescentral.com/) - color-management and creative-intent consistency.
- [Stable Virtual Camera](https://stable-virtual-camera.github.io/) - camera trajectory and viewpoint-consistency research.
- [MovieGenBench](https://github.com/facebookresearch/moviegenbench) - video and audio generation evaluation dimensions.
- [qiaomu-artist-style](https://github.com/joeseesun/qiaomu-artist-style) - comparative research on artist and visual-style descriptors.
- [seedance2-skill](https://github.com/dexhunter/seedance2-skill) - comparative research on multimodal Seedance prompting patterns.
- [NeoDomain public showcase](https://neodomain.cn/video-works-view?id=211) - public workflow presentation used only as high-level production context.
- [Adobe Story reference](https://helpx.adobe.com/uk/pdf/adobe_story_reference.pdf) - camera-movement terminology including pan, tilt, pedestal, trucking, crane/jib, whip pan, focus pull, and dolly zoom.
- [Adobe Dimension camera tools](https://helpx.adobe.com/dimension/desktop/interface/tools/camera-tools.html) - mechanical distinctions among orbit, pan, dolly, tripod pivot, roll, field of view, and dolly zoom.
- [ARRI 360 EVO](https://www.arri.com/en/camera-systems/camera-stabilizer-systems/360-evo) and ARRI cinematographer case studies - practical evidence for matching dollies, handheld, stabilized systems, cranes, and dynamic roll to scene purpose.
- [wudi/douyin_download.py](https://gist.github.com/wudi/b08ab8dbc29930673ee2cb22a87a5f18) - open-source downloader used on 2026-07-24 to retrieve the original Douyin media for local audio-visual verification.
- [张百川AI：Seedance @语法](https://v.douyin.com/TKzhEY38DNI/) - original media, timestamped audio transcript, and matching frames verified for assigning explicit purposes to image, video, and audio references.
- [张百川AI：台词标点与语气](https://v.douyin.com/TxcIiO_sKOM/) - original media, timestamped speech, and on-screen examples verified for punctuation, parenthesized internal OS, literal-asterisk stress, and speech-synchronized bracketed character actions; this project's narrower operational forms remain confirmed by the project owner.
- [张百川AI：真实感、手持与POV](https://v.douyin.com/3pr5aDOV4H8/), [高级复合运镜](https://v.douyin.com/WX-TC2rsbns/), [基础运镜](https://v.douyin.com/9lYYOjy-QmY/), [运镜速度控制](https://www.douyin.com/video/7660635843991719168), and [参考视频复刻运镜](https://www.douyin.com/video/7661622062968016128) - original media and paired audio/frame evidence used to verify movement mechanics, speed profiles, handheld/POV parameters, reference-video scope, and misuse boundaries.
- [Higgsfield HELL GRIND project](https://higgsfield.ai/@higgsfield.studio/projects/hell-grind), [Soul Cast](https://higgsfield.ai/soul-cast-intro), [Soul 2.0](https://higgsfield.ai/soul-intro), [Soul Cinema](https://higgsfield.ai/blog/soul-cinema-preview), and [Cinema Studio](https://higgsfield.ai/cinematic-video-generator) - official product/project pages used to separate static asset preproduction from video direction and to verify current Higgsfield workflow terminology. Mutable model limits and interface details require live verification.

## Authorized Martial-Action Research Inputs

The project owner confirmed permission to merge useful parts from the following repositories. Their material was translated, restructured, and compiled into this project's existing Chinese-first film-language system rather than copied as an external output template:

- [higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill) - action-reference routing, motion-input quality checks, and readable beat-density diagnostics; MIT licensed.
- [Generative-Media-Skills](https://github.com/SamurAIGPT/Generative-Media-Skills) - storyboard-first fight-scene workflow and identity/environment previsualization; MIT licensed. The high-cut 16-cell route remains research context rather than the default Wan3.0 compiler path.
- [higgsfield-skills](https://github.com/pixelab-ch/higgsfield-skills) - combat-style taxonomy, weapon and impact vocabulary, hook and example analysis; repository declares MIT.
- [higgsfield-seedance2-jineng](https://github.com/beshuaxian/higgsfield-seedance2-jineng) - fight-scene and anime-action prompt research; used with permission confirmed by the project owner.
- [skills-for-antigravity combat-design](https://github.com/omer-metin/skills-for-antigravity/tree/main/skills/combat-design) - startup/contact/recovery, telegraph, counterforce, commitment, and feedback concepts translated from game combat into film-visible body, weapon, material, sound, and aftermath mechanics; Apache-2.0 licensed.

## Project-Owner Comparative Input

- `direct-cinematic-combat-skill(1).zip` - a project-owner-provided combat-skill archive reviewed locally on 2026-07-26. The archive contained no declared license or source manifest, so no template text, code, or packaged output structure was copied. Only general mechanisms were independently rewritten and merged where they improved this project's existing rules: seven-beat combat causality, active-defense/dodge-cost/counter-opening logic, graded impact budgets, six-stage VFX lifecycle, firearm/vehicle/aerial/mecha/creature/team physical adapters, three-pass action-take review, and the separation of observed production state from generation-reference control.
- `prompt-contamination-guard(3).zip` - a project-owner-provided prompt-audit Skill reviewed locally on 2026-08-05. Its archive contained a Skill instruction file and agent metadata but no license declaration. No external template or packaged structure was copied. Independently rewritten mechanisms were merged only into the existing cold-review gate: current-source tracing, concept-cluster deduplication, cross-section control ownership, loaded-label/negative-association checks, and a deletion test that preserves unique controls and required re-anchors.
- `LIRA SKILL.md`, `ACTING SKILL.md`, and `CINEDANCE HIGGSFIELD SKILL.md` - project-owner-provided HELL GRIND companion files reviewed locally on 2026-08-06. The files were also exposed as attachments on the official project page but contained no standalone license declaration. No prompt template or packaged Skill was copied. A separate original Chinese `higgsfield-asset-preproduction` Skill was written for static characters, locations, props, reverse angles, state variants, editing and stress tests; the director Skill absorbed only compact performance, eye-life, conditional multi-subject calibration, FOV-supplement, and confirmed-adult age-boundary rules.

## Film-Language Frameworks

The following books informed the conceptual vocabulary. No book text is reproduced:

- Joseph V. Mascelli, *The Five C's of Cinematography*.
- Steven D. Katz, *Film Directing: Shot by Shot*.
- Christopher J. Bowen, *Grammar of the Shot*.
- David Bordwell, Kristin Thompson, and Jeff Smith, *Film Art*.
- Jay Rose, *Producing Great Sound for Film and Video*.

Named films, filmmakers, camera systems, lenses, trademarks, and model names remain the property of their respective owners. They are referenced for criticism, education, compatibility, or technical description.
