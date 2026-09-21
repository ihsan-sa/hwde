# hwde

**An AI PCB engineer for KiCad and JLCPCB.** Printed circuit boards, designed
from a written brief.

You describe the board you want in plain words. hwde researches the parts, picks
a topology, draws the schematic, lays out and routes the board, runs the
electrical and manufacturing checks, and hands you the files a factory needs to
build it. A human engineer signs off at every stage.

There is a PDF of this page with bigger pictures: [hwde-showcase.pdf](hwde-showcase.pdf).

![lumina-carrier](renders/lumina-carrier.png)

*__lumina-carrier__ — a 4-layer, 100 × 80 mm carrier board for a stage-lighting
fixture. 116 footprints. Designed by hwde, ordered from JLCPCB and fabricated.*

---

## How it works

Three pictures. The first is the route a board takes, the second is who does
which part of the work, the third is what happens at every handover.

### The pipeline

![the pipeline](diagrams/pipeline.png)

A run starts from a written brief and ends with a manufacturing package:
Gerbers, a bill of materials and a pick-and-place file. The middle stages each
produce one artefact — a requirements document, an architecture, a parts list, a
schematic, a routed board. Nothing is invented from nothing: every stage reads
the knowledge base of design rules, extracted datasheet numbers and the
factory's real capabilities. The orange dots are where a person has to look at
the work and agree before it continues.

### Who does what

![who does what](diagrams/roles.png)

The split matters. Twenty-two specialist subagents make the judgement calls —
choosing a topology, sizing a part, reviewing a schematic, reading a datasheet —
and each has a written contract for what it may decide. Sixty-odd deterministic
scripts do and check the mechanical work: they drive KiCad, run the routers,
export the Gerbers, and run every check. A script never has an opinion, and an
agent never edits a board file by hand. Everything either produces lands as a
file in one folder per board, so the whole history of a design is readable
without the tool that made it.

### The gate loop

![the gate loop](diagrams/gate.png)

Every stage ends at a gate. The gate runs the checks that apply — electrical
rules, design rules, manufacturability, and circuit simulations against stated
bounds — and it either passes or it hands the findings back to a fix loop that
reworks the artefact and tries again. A pass is not the end of it: a person
still signs off before the next stage starts. A green gate proves the checks
that ran, not the checks it lists, which is why the reports are kept per check
and not collapsed into a verdict.

---

## The boards

Fourteen boards have been taken far enough to have a laid-out, routed PCB. They
run from a five-part linear regulator to a 200 W RF power stage. Every render on
this page is made from the board file in the repository, by
[`render_boards.sh`](render_boards.sh).

| Board | What it is | Layers | Size (mm) | Stage reached |
|---|---|---|---|---|
| lumina-carrier | lighting carrier, PoE-powered | 4 | 100 × 80 | ordered, fabricated |
| pd-trigger | USB-C PD bench trigger | 2 | 48 × 30 | ordered, fabricated |
| lumina-par | RGBW PAR daughter board | 4 | 100 × 80 | verification |
| rf-de-20m | 20 MHz Class E GaN stage | 4 | 120 × 80 | manufacturability |
| sbuck-5v3a | 5 V / 3 A synchronous buck | 4 | 50 × 40 | package ready |
| usb-buck | USB device dev board | 4 | 50 × 40 | package ready |
| g0-sense | USB-C sensor node | 2 | 35.8 × 28.3 | package ready |
| stm32-blinky | minimal STM32 dev board | 2 | 50 × 40 | package ready |
| rf-term-150w | 150 W RF dummy load head | 2 | 26 × 20 | manufacturability |
| bb-adc | single-channel ADC | 2 | 54.8 × 34.9 | manufacturability |
| bb-amp | sensor amplifier chain | 2 | 48 × 28.3 | manufacturability |
| bb-buck | bare buck converter | 2 | 35 × 25 | manufacturability |
| bb-ldo | bare linear regulator | 2 | 34.7 × 34.7 | manufacturability |
| bb-mcu | bare microcontroller board | 2 | 34.8 × 22.3 | manufacturability |

"Stage reached" is where the board stopped in the pipeline, not a statement that
it is fit to release. Two boards say "ordered, fabricated" because their own files
record a JLCPCB order number that tracked through to shipped. The rest stopped
with a checked manufacturing package in hand. Sizes are the bounding box of the
board outline; not every outline is a rectangle.

### Designed, ordered and fabricated

![lumina-carrier](renders/lumina-carrier.png)

**lumina-carrier** — 4 layers · 100 × 80 mm · 116 footprints · ordered from
JLCPCB, tracked to shipped

The universal carrier for a stage-lighting fixture. It takes power over Ethernet
through a PD controller and a 100 V buck, and carries a frozen expansion
connector that a fixture-specific daughter board plugs into. The biggest board
here: 4 layers, 116 footprints, a controlled interface another board depends on.

![pd-trigger](renders/pd-trigger.png)

**pd-trigger** — 2 layers · 48 × 30 mm · 30 footprints · ordered from JLCPCB,
tracked to shipped

A bench tool. A USB-C Power Delivery sink controller negotiates with a charger
for 5, 9, 12, 15 or 20 volts, you pick the profile on the board, and the
negotiated rail comes out on a screw terminal rated for 5 A — up to 100 W. No
conversion on the board; it is a pass-through trigger.

### Harder boards

![rf-de-20m](renders/rf-de-20m.png)

**rf-de-20m** — 4 layers · 120 × 80 mm · 80 footprints · stopped at
manufacturability checks

A 20 MHz Class E RF power stage: 200 W into 50 ohms from a 40 V bus. A PWM drive
arrives on an SMA input, a GaN gate driver buffers it, one ground-referenced
eGaN FET switches, and a resonant tank plus an L-match transforms the 4.6-ohm
load line up to 50 ohms at the output SMA. The topology and the two core parts
were fixed by the owner after a costed trade study; hwde did the rest.

![lumina-par](renders/lumina-par.png)

**lumina-par** — 4 layers · 100 × 80 mm · 158 footprints · stopped at
verification

The RGBW PAR daughter board that stacks on the carrier. It is bound by the
carrier's frozen connector document — a hard input it may never redefine — and
by a re-derived power budget of 8.6 to 20 W depending on which
power-over-Ethernet class the fixture gets. The densest board here at 158
footprints, and the only one whose outline is not a rectangle. The silkscreen
warns that the board floats at the power-over-Ethernet potential, so an earthed
probe on it breaks the fixture's power negotiation.

![lumina-par, top-down](renders/lumina-par-flat.png)

*lumina-par straight down, so the routing shows.*

![lumina-carrier, bottom](renders/lumina-carrier-bottom.png)

*lumina-carrier from underneath. This board has every part on the top
side, so the back carries routing and vias and nothing else.*

### Power

![sbuck-5v3a](renders/sbuck-5v3a.png)

**sbuck-5v3a** — 4 layers · 50 × 40 mm · 44 footprints · package ready

7–18 V in, a regulated 5.0 V ±2% out at 3 A, synchronous buck. An open-frame
power module.

![rf-term-150w](renders/rf-term-150w.png)

**rf-term-150w** — 2 layers · 26 × 20 mm · 6 footprints · stopped at manufacturability checks

A 50-ohm, 150 W dummy load head, DC to 25 MHz. The element bolts to a heatsink
the user supplies; the board is only the RF launch and the mechanical interface.
Shown close to bare: one of its six footprints has a 3D model in the repository,
so the connector and the element are not drawn.

### Microcontroller boards

![g0-sense](renders/g0-sense.png)

**g0-sense** — 2 layers · 35.8 × 28.3 mm · 30 footprints · package ready,
release attestation built

A USB-C powered temperature and humidity node. USB-C supplies 5 V, an LDO makes
3.3 V, an STM32G030 running on its internal oscillator reads a Sensirion SHT4x
over I²C. The same bus comes out on a Qwiic connector; readings go out over a
UART header; programming is over SWD. Designed end-to-end in one unattended
container run.

![usb-buck](renders/usb-buck.png)

**usb-buck** — 4 layers · 50 × 40 mm · 28 footprints · package ready

An STM32F103 USB full-speed device board. Micro-B USB carries both power and
data; LED, button and an SWD header.

![stm32-blinky](renders/stm32-blinky.png)

**stm32-blinky** — 2 layers · 50 × 40 mm · 20 footprints · package ready

The simplest useful board: STM32F103, an 8 MHz crystal, one LED, an LDO and an
SWD header.

### Building blocks

Five deliberately bare boards, each one block and nothing else. They exist to be
studied and measured on a bench, so protection, filtering, indicators and spare
rails are left out on purpose.

| | |
|---|---|
| ![bb-buck](renders/bb-buck.png) | ![bb-ldo](renders/bb-ldo.png) |
| **bb-buck** · 2 layers · 35 × 25 mm · 20 footprints<br>18–30 V in, 5 V at 2 A out on a screw terminal. The converter and exactly what its datasheet requires. | **bb-ldo** · 2 layers · 34.7 × 34.7 mm · 5 footprints<br>5 V in, 3.3 V at 500 mA out, holding regulation in still air on the board's own copper. |
| ![bb-mcu](renders/bb-mcu.png) | ![bb-adc](renders/bb-adc.png) |
| **bb-mcu** · 2 layers · 34.8 × 22.3 mm · 14 footprints<br>One MCU, a 3.3 V rail in, its debug header and four GPIO. No regulation, no second rail. | **bb-adc** · 2 layers · 54.8 × 34.9 mm · 25 footprints<br>0–5 V in on a screw terminal, 12 bits or better at up to 10 kSa/s out over a 0.1-inch header. DC accuracy over speed. |
| ![bb-amp](renders/bb-amp.png) | |
| **bb-amp** · 2 layers · 48 × 28.3 mm · 14 footprints<br>A 0–20 mV differential bridge signal in, 0–3.3 V single-ended out, DC to 1 kHz. Nominally 165 V/V. | |

Two more boards — a 5 V/3 A buck and a strobe daughter board — stopped before
layout and have no PCB to show. They are in the repository at the stage they
reached.

---

## What it can and cannot do yet

This is a supervised engineering assistant, not an unattended release system.
Boards have been designed, fabricated and ordered with it, and the checker
corpus is real. It is still a system a human engineer drives and signs off.

**What holds**

- Fourteen boards from written briefs to routed layouts, including a 4-layer
  200 W RF stage and a novel 100 W USB-C PD design.
- Two ordered from a factory and fabricated, their order numbers tracked to shipped
  in their own files.
- Every check is a script with the same contract, and its findings are recorded
  per check rather than as a single verdict.
- Everything a run produced is a file in that board's folder, readable without
  hwde.

**What does not**

- A green gate proves the checks that *ran*, not the checks it lists. Read the
  per-check report, not the verdict.
- The pipeline stage a board reached is not a release certificate. Today a
  person decides what is releasable.
- There is no public manufacturability API at the factory, so that review stays
  a human step in a browser.
- Spending money is deliberately hard. One code path can place an order. It is
  2-layer only, it refuses a board that already records an order, and it will
  not run without a fresh quote, a matching design hash and a confirmation a
  person types out naming the board, the quantity and the total.
- The electrical and thermal checks are engineering screens with stated
  accuracy. They are not certification, and nothing here is safety-certified for
  mains, medical, automotive or aerospace use.

---

## How it gets better

![how it gets better](diagrams/lessons.png)

Every run writes down what broke and why, dated and tagged, and that goes into
the knowledge base the next run reads first. The rule is that a gotcha is
recorded the moment it is hit, so the next board does not pay for it again. It
is the same reason the boards above get harder as they go.

---

## Remaking any of this

- `./render_boards.sh` — every board render. One board takes about a minute.
  Needs Docker and the `kicad/kicad:10.0.5-full` image.
- `./build_docs.sh` — the flow charts and the PDF. Needs `pdflatex` and
  `pdftoppm`.

Renders are produced from the board files in this repository with KiCad's
command-line renderer. Board dimensions, layer counts and footprint counts are
read from those same files; the stage each board reached is read from its
recorded state.
