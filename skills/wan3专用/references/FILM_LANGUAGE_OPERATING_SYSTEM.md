# Film Language Operating System

purpose: compact silent decision map
authority: `knowledge/01-08` are canonical operational rules

## Use Boundary

Use this file to choose a director mechanism and the relevant knowledge modules. Do not copy its headings, tables, engine names, or routing labels into user-facing prompts.

Before generation, build a silent `Resolved Policy` table with source, category, priority, effective value, overridden rule, and reason. Host system/developer/user instructions remain non-overridable. Current project rules override Skill defaults for content, timestamp granularity, camera, and audit behavior when the standard output envelope is unaffected. The standard envelope is one legal segment heading plus five ordered sections; if a project rule asks to remove the heading or alter section count/name/order, quote both rules and their impact and ask the user to choose before generation or review. Never let a reviewer decide this conflict or promote a recommendation into a hard failure.

After conflicts are resolved, apply `knowledge/01_CORE_EXECUTION_CONTRACT.md`, task-relevant `knowledge/02-08`, this summary, then legacy V3 only when explicitly requested; at the same level use the narrower rule.

Do not load the entire legacy rulebook together with the current modules. Do not treat this summary as permission to invent a missing reference, model capability, camera setup, or story event.

## Core Pipeline

```text
Source evidence
-> Story facts
-> Director intent
-> Scene function
-> World geometry and blocking
-> Frame projection
-> Camera/lens and motivated light
-> Performance or action causality
-> Editing, dialogue and sound
-> Segment packing and model budget
-> Prompt
-> QC and retake decision
```

The output remains a prompt. The engines remain silent unless analysis is requested.

## Wan3.0 Version Gate

Before all other engines, resolve the target profile:

- 2.0: `Tmax=15s`.
- 2.5: `Tmax=30s`; when the active entry supports them, use at most 30 images, 10 videos, and 10 audio files, with no more than 50 total reference/input items. Do not inherit the 2.0 `3-6 CUT`/marker ceiling. A full 30-second multi-event narrative commonly supports 6-12 motivated CUTs; simpler content may use fewer, and count alone never proves overload. Scale per-phase model budget while preserving per-CUT clarity.

If a Wan3.0 script/prompt request does not specify the profile, ask the user to choose before analysis or compilation. Both profiles use the same downstream qualitative rules; capacity-derived CUT/BEAT planning and phase budgets scale with `Tmax`, while the available reference ceiling follows the selected profile. Keep the smallest sufficient reference set.

## Engine Order

1. **Evidence Router**: distinguish proved, implied, absent, and conflicting information.
2. **Story Fact Engine**: preserve characters, event order, dialogue, setting, props, ending, and user constraints.
3. **Director Intent Engine**: author the dramatic interpretation from the script/canon itself: scene function, governing experience, audience knowledge/emotion path, staging/camera purpose, and the relationship/power/information change at OUT. User instructions and reference provenance are constraints/evidence, not the intent.
4. **Scene Function Router**: choose one primary dramatic function before choosing technique.
5. **Geometry & Axis Engine**: build world topology, dynamic state, action axis, entrances/exits, danger lines, and crowd routes.
6. **Frame Projection Engine**: derive the current camera view, screen direction, depth planes, occlusion, focus path, and visible background.
7. **Performance Engine**: translate objective, obstacle, tactic, relationship, and reversal into playable body/prop actions.
8. **Action Causality Engine**: translate physical conflict into intent, preload, route, contact/miss, force response, recovery, and state update.
9. **Cinematography Engine**: select shot scale, camera position/height, lens perspective, depth of field, camera motion, and endpoint.
10. **Lighting/Color Engine**: select motivated source, direction, intensity, shadow, contrast, palette, and material response.
11. **Editorial/Sound Engine**: select cut reason, CUT/BEAT structure, dialogue location, sound bridge, silence, and visible OUT.
12. **Segment/Model Engine**: pack readable beats within target limits and allocate model attention.
13. **QC/Retake Engine**: detect ambiguity, drift, overload, impossible geometry, missing causality, and reference conflict.

## Director Intent Card

Silently answer:

```text
dramatic question:
viewpoint owner:
audience knows / does not yet know:
character goal and obstacle:
opening power state:
turning point:
ending power or information state:
why the camera must change:
```

Reject a shot choice that does not change information, emotion, viewpoint, conflict, scale, or consequence.

## Scene Function Router

Choose one primary function; use a secondary function only when it supports the same beat.

| Function | Frame priority | Camera/edit priority | Sound priority |
| --- | --- | --- | --- |
| Establish geography | entrances, exits, routes, hazard line | readable WS/EWS or moving reveal | environment establishes scale |
| Character recognition | face, costume, signature prop | CU/MCU with stable identity | breath, cloth, local action |
| Information reveal | hidden object or spatial fact | occlusion, `rack focus`, tilt/pan reveal, reaction cut | sound lead or narrowing field |
| Dialogue power | distance, height, shared/isolated frame | two-shot, depth staging, reaction ownership | source clarity and listener response |
| Suspense search | negative space, incomplete field | controlled scan, POV/objective alternation | off-screen cue, silence, narrow band |
| Threat entrance | route, scale, first contact with space | reveal from consequence to source | low-frequency or mechanical identity |
| Chase/escape | route, obstacle, changing distance | lead/follow/lateral tracking with screen direction | footfall/engine/wind escalation |
| Rescue | victim, route, blocked access, helper chain | geography before contact | calls, effort, tool confirmation |
| Fight | attack line, contact point, recovery space | readable MS/WS plus selected impact inserts | contact hierarchy and breath |
| Disaster/scale awe | human-scale anchor versus event | `crane rise`, or `camera dollies backward` with focal length fixed | expanding space and low-frequency mass |
| Transformation | source, stages, body/material response | stable identity plus staged reveal | phase-linked mechanical/energy sound |
| Comedy delay | serious task, unnoticed error, late reaction | locked relation or reaction cut | timing gap and restrained cue |
| Product/process | form, surface, ordered operation | stable macro/insert and exact focus | clean operation/SFX |
| Aftermath | changed object/body/space | `locked-off camera`, or measured `camera dolly-back` with focal length fixed | decay, silence, residual sound |

For an on-foot chase, draw separate runner, pursuer, and camera lanes before choosing coverage. Pressure must change through distance, route access, obstacle cost, visibility, or initiative. Reproject the runner from camera relation: an ahead-facing-back `lead tracking` view sees the runner's front/three-quarter front, a behind-looking-forward `follow tracking` view sees the back/three-quarter back, and a parallel lateral view sees the corresponding profile. In a one-take, preserve one camera start-path-end and one physically valid optical system: fixed focal length changes framing through distance, while any focal-length change requires an explicit continuous optical zoom. Compile readable running gait, look-back consequence, carried-load inertia, distinct pursuer strategies, motivated occlusion/focus handoff, and a physical exit with continuing sound; only add facial micro-performance when the framing can actually resolve it.

## Geometry And Frame Card

Maintain four separate states:

1. **World topology**: fixed set, routes, doors, seats, hazards, action axis.
2. **Dynamic world state**: people/props, facing, support, phase, velocity, contact, damage, residual VFX.
3. **Camera continuity metadata**: prior camera endpoint, look direction, axis side, lens, shot scale, motion phase.
4. **Current frame projection**: time-varying screen-left/right, depth planes, visible faces/body sides, occlusion, and background derived from the active camera. The first three states are foundation/planning data; world topology is visibly established through the first suitable CUT of a new space, while this derived projection leads every CUT description.

For every adjacent `OUT -> IN`, prove the state delta. Continuous combat cannot jump world anchor, height/step, depth order, support, grip/contact, action phase, speed, or relative screen order without a visible movement path or a valid new-camera reprojection. If the camera stays on the same axis side and the subjects do not visibly cross, their left/right order cannot flip.

Compute every CUT as a continuous camera setup, not an automatically fixed shot:

```text
world topology/dynamic state -> camera transform C(t): start/path/rotation/speed/end
-> frustum(t) cull and occlusion(t) resolve -> visible body/prop surfaces(t)
-> foreground/midground/background and screen-left/center/right over time
-> focus/eyeline/intended addressee/movement direction -> endpoint frame
```

Build world topology before coverage. In a new or unestablished space, the first suitable CUT visibly proves the plot-relevant topology through an establishing wide, POV, OTS, or other sufficient setup; it need not show every coordinate. Do not expose the topology as a floor-plan substitute. Every CUT compiles `IN -> separate camera/subject 3D paths and speed curves -> depth-plane crossing -> peak occlusion/reveal + screen slide/scale + true-background parallax/focus -> OUT braking/handoff point`. The OUT control point may settle or retain an explicit velocity vector for a motion cut. Only explicit `locked-off camera` freezes `C(t)`; declare zero camera path and no camera parallax while preserving subject-driven projection change. If a world anchor is essential, pair it in the same sentence with its current screen/depth projection or visible surface. Off-screen subjects stay in the ledger unless a sound, shadow, partial entry, light, or causal direction is perceivable in the shot.

For a directional prop, extend this projection with `camera-visible body side -> prop visible surface -> prop functional face/direction -> target/occlusion`. A front-facing actor reading a phone normally presents the phone back to a front camera; a shooter filmed from behind normally presents their back while the muzzle points away toward the target. Recompute after any camera, torso, head, wrist, or prop rotation; intentional reversals require an explicit new camera/pose relation.

Then compile a frame-reconstruction packet in the order the model should build the shot:

```text
location/subspace -> camera position/look direction/lens/shot size and true visible background
-> actual foreground/midground/background and screen-left/center/right
-> every visible named subject: visible body side/occlusion/gaze/prop surface/current task/performance state
-> one explicit dramatic change -> concurrent supporting action/focus/camera/dialogue/sound
-> visible OUT and relay
```

Descriptive state density is not temporal load. Coexisting blocking, posture, expression baseline, background activity, light, weather, and prop state may be declared together without becoming extra story events or extra seconds. Time cost comes from spoken duration, ordered state changes, camera travel, reveal/read time, contact/reaction, and settle. Use lock names and current facts; do not repeat full identity/style prose or synonymous adjectives inside every CUT.

If an opening contains four or more independently readable active subjects and their blocking, axis, addressee relation, or hazard route is not yet established, a roughly one-second WS/EWS spatial calibration is allowed. Show all required subjects and anchors in the first frame, let low-amplitude tasks or ambience continue, count it as real duration, and relay through gaze, direction, visual center, or sound. A crowd group counts as one subject unless named leads or separate fronts need tracking. Do not apply this template to three-or-fewer subjects, established geography, or an opening whose critical line/contact must happen immediately.

Coordinate terms are not interchangeable:

- `screen-left/right` = viewer-relative frame position.
- `world direction` = fixed map/route direction.
- `character's left/right` = anatomical body side.
- `foreground/background` = camera-relative depth.

For multi-character, dialogue, doorway, adjacent-space, entrance/exit, handoff, or competing-eyeline CUTs, run a blocking-frustum-addressee gate. This is a stricter form of the frame-reconstruction packet, not a separate output section:

```text
silent world-anchor verification -> camera/frustum roster -> image-plane position/body surface/true background
-> speaker/addressee pair -> visible third-party task or perceivable off-screen evidence -> action and OUT
```

Keep dialogue, threshold/observation, handoff/task, and movement axes separate. Adjacent close-ups, OTS/reaction cuts, and matched eyelines imply a speaker-listener pair; a third person at the speaker's eyeline endpoint can override a textual addressee. Repair first through blocking, frustum, a readable three-person establish, or a more motivated scene. An object/body-part insert ends with its declared setup and does not authorize an undeclared follow-through camera.

## Frame Composition Card

Use only mechanisms that serve the scene:

| Mechanism | Use |
| --- | --- |
| centered symmetry | authority, ritual, threat, product |
| thirds + negative space | absence, unseen threat, social distance |
| deep staging | simultaneous foreground/midground/background information |
| foreground occlusion | concealment, surveillance, motivated reveal |
| frame within frame | confinement, hierarchy, divided attention |
| leading lines | route, danger, pursuit, fate |
| top-down map | route, crowd pressure, blocked escape |
| low-angle scale | authority, machine, creature, monument |
| high-angle vulnerability | isolation, exposure, entrapment |
| tilted horizon / Dutch angle | actual perceptual instability, not generic style |

Describe moving shots in reveal order:

```text
initial field -> motion/parallax/occlusion -> new object/person -> final focus and OUT
```

## Camera Semantics

The Chinese noun `镜头` is not a canonical technical unit. Resolve it as `CUT` (edit/setup), `camera` (viewpoint/movement), `lens/focal length` (optics), `shot size` (framing scale), or `Frame` (one image state) before compiling.

Do not use ambiguous Chinese camera verbs alone. Resolve them mechanically:

| Intended operation | Canonical meaning |
| --- | --- |
| `dolly/truck forward/back` | camera translates; state whether focal length stays fixed |
| `zoom in/out` | focal length changes while camera position stays fixed |
| `pan` | camera yaws left/right from a fixed origin |
| `tilt` | camera pitches up/down from a fixed origin |
| `roll / Dutch angle` | horizon rotates around the optical axis |
| `lateral truck` | camera translates sideways |
| `follow tracking` | camera follows behind/alongside a named subject |
| `lead tracking` | camera moves ahead of a named subject while facing it |
| `pedestal/boom` | camera translates vertically while lens direction is defined |
| `crane` | boom/arc movement; specify path, height, and endpoint |
| `orbit` | camera translates around a named center; subject does not automatically spin |
| `rack focus` | focus plane moves; camera position does not |
| `locked-off camera` | camera is fixed; actors/environment may move |
| `handheld` | camera micro-motion; specify amplitude, frequency, and body/step source |
| `slow motion` | temporal retiming of action, not a slow camera move |
| `speed ramp` | temporal speed changes at named action phases |
| `dolly zoom` | camera translation plus inverse focal change while subject size is held |
| `hard/direct cut` | edit event, not camera movement |
| `whip pan` | rapid pan between named endpoints; specify whether a hidden cut exists |
| `bullet time` | slowed/frozen action plus a separately defined moving virtual camera |

Compile:

```text
motion/rig + route + direction + speed profile
+ subject frame hold + start frame + endpoint + story result
```

## Cinematography Decision Card

Choose from visible requirements, not prestige labels:

- **Camera distance** controls intimacy and readable geography.
- **Focal length** controls perspective and field of view together with distance.
- **Diagonal FOV** may supplement focal length for disambiguation, but never replaces focal length, format, camera distance, subject scale, or the visible perspective result. When both are stated they must be physically consistent.
- **Camera height** controls power, vulnerability, and body/action readability.
- **Depth of field** controls information priority; do not blur required crowds or hazards.
- **Lens distortion/compression** must support the story and subject anatomy.
- **Camera body/lens names** are visual shorthand only; always include visible highlight, contrast, skin, flare, edge, and depth characteristics.

For dialogue, choose shared two-shot, depth staging, foreground pressure, height difference, negative space, lateral reframe, reaction hold, or motivated locked-off based on relationship and semantic ownership.

For action, the camera has one or two jobs per CUT:

- establish geography;
- show intent/preload;
- track the route;
- confirm contact/evasion;
- show consequence.

Choose framing from the required visible evidence. If hands, support feet, both bodies, a long weapon's functional end, and the contact point must be read together, use MLS/WS or an equivalent full-body composition; a tight frame cannot claim evidence outside its crop. A decisive slow-motion combat window is atomic from deceleration through contact and the first force response; do not cut, hide-cut, pause, or restart the preload inside it.

## Lighting And Color Card

Every independent segment carries a complete base-style technical packet before the timeline:

```text
camera system + sensor/film or virtual-camera format + aspect ratio
+ lens rendering/focal tendency/depth/diffusion/highlight behavior
+ motivated sources/directions + key/ambient-practical color temperatures
+ shadow/negative fill + selected contrast ratio
+ atmosphere/aerial perspective + material microtexture/optical response
+ palette relation/saturation + black toe/highlights + LUT/grade result
```

Live-action/photoreal work names a concrete cinema camera or film-format baseline. Animation/CG names a virtual cinema camera and equivalent format. CUT-level focal length does not replace this capture baseline. Generic labels such as `live-action cinematic style`, `cinematic grading`, `warm light`, or `premium texture` are invalid alone.

Select rather than stack texture terms. Strong aerial perspective requires a depth field and atmospheric medium; anisotropy requires aligned material structure; caustics require a light source, refractive/reflective carrier, receiver, and movement logic; 8:1 contrast and compressed blacks must preserve required faces, hazards, and action routes.

Compile light as:

```text
source + world/screen direction + intensity
+ shadow quality + contrast/negative fill
+ atmosphere + material/skin response
```

`暖光/冷光/电影光` alone is invalid.

Compile color as:

```text
dominant environment color + character/prop secondary color
+ danger/accent color + warm/cool relationship
+ LUT/stock-like visible behavior
```

Use HEX only for stable product/UI/brand requirements. Style names and painter names must become visible line, edge, palette, composition, texture, light, and mood.

## Performance Card

Keep a full acting master profile in the silent project ledger: confirmed adult age when useful, regional/language environment, accent, timbre/register/resonance, speech habits, physiological voice baseline, body/center, objective/obstacle/tactic, triggered habits, public mask/private crack, gait, eye life, stress transformation, status behavior, and inherited residue. Rewrite it for the current scene; do not paste the full profile into every generation prompt. All functional, camera- or sound-readable layers may coexist when they do not conflict with dialogue, action, or framing.

Every named voice uses a five-part identity: `regional context -> accent and audible mechanics -> timbre/register/resonance -> pace/pause/stress/ending habits -> stable physiology plus current condition`. User/canon outranks an assigned voice reference, which outranks directly audible evidence, which outranks conservative inference. Unsupported locality stays broad and uses the target language's standard accent; never infer a strong dialect from face, clothing, occupation, or genre stereotype. Keep stable voice identity across segments, but locate crying, breathlessness, pain, fatigue, illness, intoxication, or recovery changes in the CUT where the story causes them.

Eye life is causal rather than decorative: name the gaze target, let thought lead the head/body shift, choose blink behavior from pressure and attention, and request a natural catchlight only when the shot can read it. Do not convert this into random blinking, accidental lens contact, or a serial checklist. Unknown ages remain unknown; an adult-age anchor applies only to a confirmed adult and never silently changes a canonical minor.

Translate emotion into playable layers:

```text
goal -> obstacle -> tactic -> beat reversal
-> face -> breath -> body/weight -> prop/space action
-> rhythm -> mask versus leak -> new state
```

Keep face and body distinct, but treat face, breath, body, prop, rhythm, and reaction as a selection pool rather than a checklist. Example mechanism: deadpan face + fast purposeful walk.

Estimate performance load before writing a timecode:

```text
speech floor = audible spoken characters / 5.5 + explicit pauses
required time = speech floor
+ serial action/reaction/information/camera time
+ max(0, longest concurrent lane - speech floor)
```

Count only text actually spoken: exclude speaker labels, punctuation, quotation marks, spaces, and `【action】`; expand numbers and Latin tokens by their audible reading. An action that waits for the previous one is serial. Movement under dialogue, a low-amplitude listener response, persistent ambience, and a non-competing camera follow may run in parallel and add only excess beyond the speech window. Never divide total duration evenly by CUT count. A reaction of one second or less receives one dominant reflex, not a full sequence of blink, breath, swallow, gaze, hand, and turn. Close-up increases readability; it does not authorize extra performance layers.

For dialogue:

```text
pre-line trigger -> line begins -> action under line
-> listener responds at semantic turn -> line ends on a new state
```

The image may belong to the listener, prop, or space while the named speaker continues through J-cut/L-cut.

## Action Causality Card

Compile:

```text
intent -> preload -> route -> contact/block/miss
-> force response -> recovery/imbalance -> state update
```

Every visible action names:

```text
actor + body part/tool + support/force source + route
+ target/contact or miss + receiver response + recovery + sound
```

Defense redirects force. Evasion changes distance, angle, footing, resource, or initiative. Counterattack uses an opening created by the prior action.

Choose one primary martial route:

- unarmed;
- weapon;
- energy.

Add at most one physical adapter:

- firearm: muzzle line, cover, recoil, reload/ammunition state;
- vehicle: grip, traction, suspension, route width, braking/ramming force;
- aerial: altitude, thrust/lift, turn radius, descent/recovery;
- heavy/mecha: mass, support feet, joint load, hydraulic/motor preload;
- creature: anatomy, limb/wing/tail support, bite/claw path, recovery;
- team/multi-front: objective, lanes, handoff, friendly-fire/occlusion logic.

Feedback budgets are internal labels:

- probe/light;
- medium;
- heavy;
- decisive/finisher.

They control body/material/camera/sound response, not plot importance by themselves.

For combat VFX, silently choose an auxiliary, primary, or decisive maximum. Compile visible evidence as:

```text
source/carrier -> optional core/body/decaying edge
-> path/contact boundary -> dynamic local light/material response
-> synchronized residual decay
```

Do not expose S/A/B grades or generic render-engine toggles. Use only the layers needed by the effect and keep the decisive tier rare.

For a combat one-take, 单镜模式 uses one untimed `CUT 1` with ordered untimed BEATs; 多镜模式 uses one `CUT 1（0-T秒）` with contiguous BEATs at the resolved timestamp granularity. Motivate every camera turn, height change, and focus handoff through gaze, attack/evasion path, visible spatial passage, contact result, or scale reveal. Reverse direction through deceleration/settling/orbiting a named anchor; carry camera endpoint, action phase, VFX attachment, intensity, material response, and residual state into the next BEAT.

For long weapons, preserve a continuous witness chain from owner and front/rear grips through the shaft to the functional end/contact surface, force direction, and recovery or release order. When research is used, keep source URLs and claim mappings in the silent review ledger; prompt-only output remains exactly the segment heading plus five fixed sections and ends after `【画面限制】`.

For camera-rich combat, separate geography invariants from coverage topology. Preserve world anchors, facing, action axis, pressure route, and landmarks; vary camera azimuth, height, distance, path/tracking owner, and proof task only when the new coverage proves space, intent, contact, reversal, scale, or consequence. If adjacent major CUTs repeat most coverage attributes without an information delta, merge or redesign; a motivated visible change normally alters at least two attributes. Let an attack, body, or force vector briefly control `roll/pitch/yaw`, then settle on the consequence.

Treat selected arena elements as cumulative state machines: `initial -> observed/loaded -> used -> changed state -> tactical consequence -> payoff`. Reserve full physiological acting and synchronized sound confirmation for decisive hits. In asymmetric-scale fights, keep the smaller combatant as the continuing camera anchor, use functional giant-body fragments for most contact coverage, and spend a wide shot only when scale must be established or upgraded.

Combat automatically uses the version-specific timeline defined in `knowledge/05` and `knowledge/06`: untimed ordered CUT/BEAT structure for 2.0, and contiguous CUT timecode under `Resolved Policy.timestamp_policy` for 2.5. The 2.5 default is integer-preferred, while explicit project rules may allow decimal seconds or frame events.

## Editing And Timeline Card

Definitions:

- independent segment = one model request;
- CUT = edit/camera unit inside the segment;
- BEAT = internal state change without an edit;
- action phase = physical micro-stage, not automatically a CUT.

Every CUT carries one explicit change. Supporting changes are allowed when they prepare, drive, confirm, or relay that change.

Use cuts for:

- information change;
- emotional ownership change;
- viewpoint change;
- conflict escalation;
- scale reveal;
- action/result confirmation.

Relay adjacent CUTs with an already moving or sounding carrier: limb/weapon path, gaze, focus, debris, smoke, real foreground occlusion, or sound cue.

Apply a motivated-cut gate. A `CUT N` label already declares an edit, so explicit `hard/direct cut` is reserved for stopping setup interpolation, releasing a static end-frame's old camera control, or creating intentional narrative contrast. Continuous action uses match-on-action, direction/contact continuity, matched eyeline, visual-center/focus continuity, or sound bridge. Real foreground occlusion may conceal a cut, but never invent a wipe merely to justify one. With neither continuity carrier nor intentional discontinuity, continue the setup or merge the CUTs.

For 多镜模式, automatically enter long-form timecode mode when planned `T>=20s` and the segment has at least six CUTs, at least three irreversible ordered events, a mandatory post-climax ending, a leave-return-rescue/consequence chain, cross-space movement, or evidence of reordered/truncated generation. Read `Resolved Policy.timestamp_policy`: integer boundaries are the readable default, decimal seconds or `Frame T` are allowed when the project requires them, and pure integer-only validation applies only when explicitly requested. Every policy starts at 0, remains monotonic and gap/overlap-free, and ends exactly at `T`; avoid meaningless precision. Build cause-before-result precedence and latest-completion milestones. Schedule backward from the mandatory visible OUT: reserve consequence first, then climax, then allocate setup and ordinary reactions. If silent rehearsal exceeds a CUT interval, reduce, overlap, or move semantic work; timestamps do not accelerate performance.

Persistent wind, suction, rain, fire, alarm, or pressure is one cross-CUT state machine. After the transition is established, select only one or two directional evidence channels per CUT. Physical exits keep entities opaque and use route, depth checkpoints, scale change, force-driven posture, and real occlusion or frame exit instead of abstract dissolve language.

Use montage as an editing structure, not a camera move. State the compressed process, repeated visual unit, progression rule, and final changed state.

## Sound Card

Separate:

- diegetic environment/action/voice;
- non-diegetic music when requested;
- off-screen source;
- subjective narrowing/ringing;
- sound bridge;
- low-frequency scale/threat;
- silence and abrupt stop.

Place sounds at the visible cause. Sound may lead an edit, but source attribution must remain clear.

Reference audio can be:

- final BGM;
- silent beat guide;
- SFX guide;
- ambience bed;
- voice anchor.

A voice anchor controls directly audible accent, timbre, resonance, register, speaking rhythm, stress, and microphone texture. Keep the attachment on its own lock line; the character lock names the anchor and adds the current physiological state. Exact dialogue and any change in cry, breath, pain, hesitation, or loudness remain timeline events.

Never let a silent control track become audible final BGM.

## Famous-Scene Feeling Compiler

Translate the user's “feeling” into mechanisms, not copied protected expression:

| Mechanism | Reusable effect |
| --- | --- |
| threshold breach | safety boundary fails and power enters |
| shadow authority | power is shown through blocking, delay, and reaction ownership |
| time-slice decision | decisive instant expanded while causality stays clear |
| power-table staging | seating, height, distance, and listening define hierarchy |
| long-take entrapment | route closes as camera and character traverse space |
| scale inversion | small person versus overwhelming object/event |
| delayed consequence | action occurs, reaction/aftermath reveals its meaning later |
| memory match cut | shape/motion/sound connects present and memory |
| false calm -> rupture | stable task and sound field interrupted by one irreversible event |
| off-screen threat -> reveal | sound/effect precedes source |
| foreground betrayal | trusted foreground element becomes obstruction/threat |
| reaction ownership reversal | camera leaves the speaker for the person whose knowledge changes |
| spatial trap reveal | ordinary geography is re-read as blocked escape |
| repeated ritual variation | same action returns with one changed detail |
| subjective/objective break | POV belief is contradicted by objective geography |
| impossible stillness | large-scale motion stops around one readable decision |

Do not reproduce exact characters, dialogue, costume, production design, choreography, or shot order from a named work unless authorized material and policy permit it.

## Genre And Special Routes

Use compact routes only when triggered:

| Trigger | Mechanism |
| --- | --- |
| face-to-face reveal | shared axis -> withheld face/info -> reaction ownership |
| duel | geography -> intent -> exchange -> consequence -> reset/new advantage |
| chase | route map -> obstacle -> distance change -> failed option -> exit/turn |
| farewell | shared task -> distance grows -> sound/gesture persists -> absence |
| rescue | victim state -> blocked route -> tool/team relay -> contact -> extraction |
| weak hero | capability gap -> improvised tactic -> cost -> narrow reversible gain |
| task montage | repeated unit -> escalating variation -> cumulative visible result |
| transformation | stable identity -> trigger -> staged body/material change -> cost/residual |
| street search | objective scan -> misleading cue -> spatial reframe -> discovery |
| shock arrival | off-screen cue -> reactions -> scale/source reveal |
| planned long take | route map -> contiguous BEAT markers -> motivated turn/height/focus handoff -> state-continuous settled OUT |
| mirror monologue | reflection geometry -> mask/leak -> focus/angle change -> self-recognition |
| parallel desire montage | matched actions/objects/sounds reveal aligned or opposing goals |
| retro-future/atompunk | era craft/material logic + speculative function + lived wear |
| zombie/creature cleanup | procedure, hazard, tool topology, contamination route, aftermath |
| LED-face robot | body performance + display state + voice source kept distinct |
| mounted chase | rider/animal support, gait, route, camera vehicle, obstacle timing |
| absurd apocalypse romance | sincere relationship task inside escalating world contradiction |
| AI-actor meta scene | external control inferred through gaze, voice, interface sound, not unexplained text |
| prompt-world loading | staged environment materialization with spatial order and residual state |
| black-void boot-up | identity anchor -> light/source activation -> space construction |
| reference-reading dialogue | readable source ownership, eyeline, lip-sync, listener/object reaction |
| creator cutaway | separate real-world camera grammar and clear cause/effect bridge to generated scene |

## Model Budget And Retake

Choose one primary model spend:

- identity fidelity;
- motion boldness;
- scene density.

Choose at most one secondary spend. Reduce or split the rest.

For a generated take, choose:

1. keep;
2. fix in post;
3. edit one layer;
4. re-roll;
5. rewrite.

Change one variable per retake when possible. After the same failure repeats twice, diagnose the causal instruction rather than adding adjectives.

## Output And QC

Canonical visible sections:

```text
【角色/场景/素材锁定】
【基础风格】
【运镜与时间轴】
【声音设计】
【画面限制】
```

`【角色/场景/素材锁定】` is first, and each actual attachment/reference item occupies its own line. Build an entity registry first: each character, scene, prop, or text asset has one primary description line per independent segment. When a primary image controls that entity's identity, appearance, or topology, merge its handle, canonical description, and control dimensions into the same line; supplementary references only state incremental dimensions. `【基础风格】` follows it and remains before the timeline.

Each named character receives one compact primary character line in the lock section with regional context, accent, timbre, speech habits, and current physiology, even if that character is silent in the current segment. If a primary character image exists, that image line is the character line rather than a second restatement. Voice identity never causes speech by itself; dialogue remains a timeline event. Undifferentiated background crowds do not need individual voice profiles.

Composition, focus path, dialogue, action, cut reason, and visible OUT remain inside `【运镜与时间轴】`.

Every 多镜模式 independent segment begins that timeline section with five compact model-facing lines before CUT 1: `前提` for current-segment facts, `核心关系` for behavioral/power/affection/conflict asymmetry and change, `导演意图` for the compiler-authored dramatic interpretation `scene function -> audience knowledge/emotion path -> staging/camera purpose -> relationship/power/information OUT`, `演员指令` for each named actor's playable objective/tactic/body task/escalation, and `对白规则` for the exact language/source/line whitelist and cross-CUT continuity. User requests, original-footage/reference provenance, prompt workflow and model needs never substitute for director intent. These are not extra top-level sections or exposed chain-of-thought. They declare global semantics once; event-specific action, performance, dialogue trigger/lip-sync/listener reaction, camera proof and OUT remain in each CUT.

Resolve `review_mode` before drafting: default `critical-only`, explicit every-segment review `full`, explicit disable `off`. Ordinary drafts and continuations front-load facts, topology, camera/frustum projection, dialogue/action capacity, clear paths, contact response, CUT relay and OUT, then run one Fast Preflight Card; PASS stops immediately, while failure gets one focused repair and only failed assertions plus envelope gates are rerun. Narrow repairs use an explicit delta contract and diff check. Long drafts build one global map, freeze each passing segment after adjacent-boundary validation, and never semantically rescan the whole frozen document. They do not create `PROJECT_RULES.md` or wait for a reviewer. Under `critical-only`, review only explicit final/submission versions, the first reusable pilot segment for later batch work, or an irreversible cross-segment handoff; complexity alone is not critical. When review is active, mechanical-preflight then seal exactly one legal segment heading plus five sections without an extra same-context semantic sweep; require one uniquely embedded candidate, BOM-safe exact equality, `EXACT_MATCH=True`, `MECHANICAL_PASS=True`, and a snapshot hash. Multi-segment review processes one segment per packet/state and waits for explicit user acceptance before the next. One snapshot gets one fresh reviewer; first-round PASS stops immediately, and only an actual structural repair may trigger one terminal second round. Treat the candidate as one semantic field and preserve unique controls and required cold-start anchors. GPT-agent hosts perform sealed internal acceptance only when the route activates it and never pretend an ordinary draft was cold-reviewed.

Before delivery, use `knowledge/08_MODEL_QC_REPAIR.md` and verify:

- no bare ambiguous camera/coordinate/action term;
- no conflict between ledger facts and reference control;
- no unsupported inference from still images;
- no impossible background/axis relation;
- no new space missing a visible topology establishment, and no CUT missing the relevant camera start/path/end, dynamic frustum/occlusion, body-facing, or intended dialogue addressee where ambiguity exists;
- no third party accidentally completing a speaker-listener eyeline pair;
- no object/body-part insert silently extending into an undeclared follow shot;
- no actor/prop/action without a named subject and route;
- no dialogue outside the timeline;
- no 2.0 fight with visible timestamps; no 2.5 timed work whose ranges violate the resolved granularity or fail to start at0, remain monotonic/contiguous, and end at the exact duration;
- no crowd disappearance in a visible wide shot;
- no completed/future production history in the model prompt;
- no model specification invented from memory;
- no unnecessary English or internal library label in the visible output.
- no final prompt released before the project packet review and author-side QC are complete.
