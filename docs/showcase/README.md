# hwde

**An AI PCB engineer for KiCad and JLCPCB.** Printed circuit boards, designed
from a written brief.

You describe the board you want in plain words. hwde then researches the parts,
picks a topology, draws the schematic, and lays out and routes the board. It
runs the electrical and manufacturing checks, and hands you the files a factory
needs to build it. A human engineer signs off at every stage.

There is a PDF of this page with bigger pictures: [hwde-showcase.pdf](hwde-showcase.pdf).

![lumina-carrier](renders/lumina-carrier.png)

*__lumina-carrier__ is a 4-layer carrier board for a stage-lighting fixture,
100 × 80 mm with 116 footprints. hwde designed it, and it was ordered from
JLCPCB and fabricated.*

---

## How it works

Three pictures follow. The first is the route a board takes, the second is who
does which part of the work, and the third is what happens at every handover.

### The pipeline

![the pipeline](diagrams/pipeline.png)

A run starts from a written brief and ends with a manufacturing package of
Gerbers, a bill of materials and a pick-and-place file. Each stage in between
produces one file of its own, and in order those are a requirements document, an
architecture, a parts list, a schematic and a routed board. Before a stage
produces anything it reads the knowledge base of design rules, datasheet numbers
and what the factory can really make. The orange dots mark where a person has to
look at the work and agree before it goes on.

### Who does what

![who does what](diagrams/roles.png)

The work is split in two. Twenty-two specialist subagents make the judgement
calls, like choosing a topology, sizing a part, reviewing a schematic or reading
a datasheet, and each one has a written contract for what it may decide. About
sixty scripts do and check the mechanical work, and they are all deterministic.
They drive KiCad, run the routers, export the Gerbers and run every check. A
script never has an opinion, and an agent never edits a board file by hand.
Whatever either of them produces lands as a file in one folder per board, so you
can read a design's whole history without the tool that made it.

### The gate loop

![the gate loop](diagrams/gate.png)

Every stage ends at a gate. The gate runs the checks that apply to that stage,
which are the electrical rules, the design rules, manufacturability and circuit
simulations against stated bounds. It either passes, or it hands the findings
back to a fix loop that reworks the file and tries again. A pass is not the end
of it, because a person still signs off before the next stage starts. A green
gate only proves the checks that actually ran, so the reports are kept one per
check instead of being collapsed into a verdict.

---

## The boards

Fourteen boards got far enough to have a laid-out, routed PCB. They run from a
linear regulator with five parts to a 200 W RF power stage. Every render on this
page was made from the board file in the repository, by
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

"Stage reached" says where the board stopped in the pipeline, and it does not
say the board is fit to release. Two boards say "ordered, fabricated" because
their own files record a JLCPCB order number that tracked through to shipped.
The rest stopped with a checked manufacturing package in hand. Each size is the
bounding box of the board outline, and not every outline is a rectangle.

### Designed, ordered and fabricated

![lumina-carrier](renders/lumina-carrier.png)

**lumina-carrier** — 4 layers · 100 × 80 mm · 116 footprints · ordered from
JLCPCB, tracked to shipped

This is the universal carrier for a stage-lighting fixture. It takes power over
Ethernet through a PD controller and a 100 V buck, and it carries a frozen
expansion connector that a fixture-specific daughter board plugs into. It is the
biggest board here, with 4 layers and 116 footprints, and another board depends
on the connector it sets.

![pd-trigger](renders/pd-trigger.png)

**pd-trigger** — 2 layers · 48 × 30 mm · 30 footprints · ordered from JLCPCB,
tracked to shipped

This one is a bench tool. A USB-C Power Delivery sink controller negotiates with
a charger for 5, 9, 12, 15 or 20 volts, and you pick the profile on the board.
The negotiated rail comes out on a screw terminal rated for 5 A, so up to 100 W.
The board converts nothing. It just passes the rail through.

### Harder boards

![rf-de-20m](renders/rf-de-20m.png)

**rf-de-20m** — 4 layers · 120 × 80 mm · 80 footprints · stopped at
manufacturability checks

A 20 MHz Class E RF power stage that puts 200 W into 50 ohms from a 40 V bus. A
PWM drive arrives on an SMA input, a GaN gate driver buffers it, and one
ground-referenced eGaN FET switches. A resonant tank and an L-match transform
the 4.6-ohm load line to 50 ohms at the output SMA. The owner fixed the topology
and the two core parts after a costed trade study. hwde did the rest.

![lumina-par](renders/lumina-par.png)

**lumina-par** — 4 layers · 100 × 80 mm · 158 footprints · stopped at
verification

The RGBW PAR daughter board that stacks on the carrier. The carrier's connector
document is frozen, so this board takes it as given and may not redefine it. Its
power budget of 8.6 to 20 W was re-derived here, and depends on the
power-over-Ethernet class the fixture gets. It is the densest board here at 158
footprints, and the only one whose outline is not a rectangle. The silkscreen
warns that the board floats at the power-over-Ethernet potential, because an
earthed probe breaks the fixture's power negotiation.

![lumina-par, top-down](renders/lumina-par-flat.png)

*The same board from straight above, so the routing shows. It has four layers
and 158 footprints, routed to the same rules as everything else.*

![lumina-carrier, bottom](renders/lumina-carrier-bottom.png)

*lumina-carrier from underneath. Every part sits on the top side of this board,
so the back carries routing and vias and nothing else. This is how the factory
sees it.*

### Power

![sbuck-5v3a](renders/sbuck-5v3a.png)

**sbuck-5v3a** — 4 layers · 50 × 40 mm · 44 footprints · package ready

A synchronous buck that takes 7–18 V in and holds 5.0 V ±2% at 3 A out. It is
an open-frame power module.

![rf-term-150w](renders/rf-term-150w.png)

**rf-term-150w** — 2 layers · 26 × 20 mm · 6 footprints · stopped at manufacturability checks

A 50-ohm, 150 W dummy load head for DC to 25 MHz. The element bolts to a
heatsink the user supplies, so the board is only the RF launch and the
mechanical interface. It renders close to bare because none of its six footprints has a 3D model
the renderer could find, so the connector and the element are not drawn.

### Microcontroller boards

![g0-sense](renders/g0-sense.png)

**g0-sense** — 2 layers · 35.8 × 28.3 mm · 30 footprints · package ready,
release attestation built

A temperature and humidity node that runs off USB-C. USB-C supplies 5 V and an
LDO makes 3.3 V from it, and an STM32G030 on its internal oscillator reads a
Sensirion SHT4x over I²C. The same bus comes out on a Qwiic connector, the
readings go out over a UART header, and you program it over SWD. hwde designed
this one end to end in a single unattended container run.

![usb-buck](renders/usb-buck.png)

**usb-buck** — 4 layers · 50 × 40 mm · 28 footprints · package ready

An STM32F103 board that talks USB at full speed. The Micro-B socket carries both
power and data, and there is an LED, a button and an SWD header.

![stm32-blinky](renders/stm32-blinky.png)

**stm32-blinky** — 2 layers · 50 × 40 mm · 20 footprints · package ready

The simplest useful board here. It has an STM32F103, an 8 MHz crystal, one LED,
an LDO and an SWD header.

### Building blocks

These five boards are deliberately bare, each one carrying a single block and
nothing else. They are there to be studied and measured on a bench, so they
leave out protection, filtering, indicators and spare rails on purpose.

| | |
|---|---|
| ![bb-buck](renders/bb-buck.png) | ![bb-ldo](renders/bb-ldo.png) |
| **bb-buck** · 2 layers · 35 × 25 mm · 20 footprints<br>It takes 18–30 V in and gives 5 V at 2 A out on a screw terminal. It carries the converter and exactly what its datasheet requires. | **bb-ldo** · 2 layers · 34.7 × 34.7 mm · 5 footprints<br>It takes 5 V in and gives 3.3 V at 500 mA out, holding regulation in still air on the board's own copper. |
| ![bb-mcu](renders/bb-mcu.png) | ![bb-adc](renders/bb-adc.png) |
| **bb-mcu** · 2 layers · 34.8 × 22.3 mm · 14 footprints<br>One MCU with a 3.3 V rail coming in, its debug header and four GPIO. There is no regulator and no second rail. | **bb-adc** · 2 layers · 54.8 × 34.9 mm · 25 footprints<br>0–5 V in on a screw terminal, and 12 bits or better at up to 10 kSa/s out over a 0.1-inch header. It trades speed for DC accuracy. |
| ![bb-amp](renders/bb-amp.png) | |
| **bb-amp** · 2 layers · 48 × 28.3 mm · 14 footprints<br>It takes a 0–20 mV differential bridge signal and gives 0–3.3 V single-ended out, from DC to 1 kHz. The nominal gain is 165 V/V. | |

Two more boards stopped before layout and have no PCB to show, a 5 V/3 A buck
and a strobe daughter board. Both are in the repository at the stage they
reached.

---

## What it can and cannot do yet

hwde is an engineering assistant, and it does not release a board by itself. A
human engineer drives it and signs off at every stage. Two of the boards above
were designed with it, ordered from a factory and fabricated.

**What holds**

- Fourteen boards went from a written brief to a routed layout, including a
  4-layer 200 W RF stage and a novel 100 W USB-C PD design.
- Two of them were ordered from a factory and fabricated, and their own files
  record the order numbers tracked through to shipped.
- Every check is a script, and they all follow the same contract. The findings
  are kept per check rather than as a single verdict.
- Everything a run produces is a file in that board's folder, and you can read
  it without hwde.

**What does not**

- A green gate only proves the checks that *ran*. Read the report for each check
  rather than the verdict.
- The stage a board reached is not a release certificate. A person decides what
  is fit to release.
- The factory has no public API for its manufacturability review, so someone
  still does that step by hand in a browser.
- Spending money is deliberately hard. One code path can place an order, and it
  handles 2-layer boards only. It refuses a board whose files already record an
  order, and it will not run without a fresh quote and a matching design hash. A
  person also has to type out a confirmation naming the board, the quantity and
  the total.
- The electrical and thermal checks are engineering screens, and each states its
  own accuracy. None of them is a certification, and nothing here is
  safety-certified for mains, medical, automotive or aerospace use.

---

## How it gets better

![how it gets better](diagrams/lessons.png)

Every run writes down what broke and why, with a date and a tag, and that goes
into the knowledge base the next run reads first. The rule is to record a gotcha
the moment you hit it, so the next board does not pay for it again.

---

## Remaking any of this

- `./render_boards.sh` makes every board render. One board takes about a minute,
  and it needs Docker and the `kicad/kicad:10.0.5-full` image.
- `./build_docs.sh` makes the flow charts and the PDF. It needs `pdflatex` and
  `pdftoppm`.

The renders come from the board files in this repository, drawn by KiCad's
command-line renderer. The dimensions, layer counts and footprint counts are
read from those same files, and the stage each board reached is read from its
recorded state.
