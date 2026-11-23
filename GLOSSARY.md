# Smart Traffic Signals

A simulated, AI-controlled corridor of signalised intersections in central Ulaanbaatar, serving vehicles and pedestrians under hard safety rules.

## Road network

**Corridor**:
The connected set of Signal Sites the system controls and shows, a single stretch of road rather than the whole city.
_Avoid_: Area, zone, map

**Signal Site**:
Any place in the Corridor where signals control traffic: an Intersection or a Mid-block Crossing.
_Avoid_: Light, junction, node

**Intersection**:
A Signal Site where roads cross.
_Avoid_: Crossroads, junction

**Mid-block Crossing**:
A Signal Site with a signalised Crosswalk and no crossing road.
_Avoid_: Pedestrian light, zebra

**Neighbour**:
A Signal Site directly connected to another by a road with no Signal Site between them.
_Avoid_: Next crossroads, adjacent light

**Approach**:
One incoming direction of traffic into a Signal Site, such as the northbound approach.
_Avoid_: Way, road, side, lane

**Movement**:
A path a vehicle or pedestrian takes through a Signal Site, from one Approach to one exit, such as the north-to-east left turn.
_Avoid_: Turn, direction

**Crosswalk**:
A marked place where pedestrians cross one road at a Signal Site.
_Avoid_: Zebra, crossing

## Signals

**Signal Group**:
A set of signal heads that always show the same colour at the same time.
_Avoid_: Light, traffic light

**Vehicle Signal**:
A Signal Group that controls vehicle Movements.
_Avoid_: Car light

**Pedestrian Signal**:
A Signal Group that controls a Crosswalk.
_Avoid_: Human light, walk light

**Phase**:
A set of Signal Groups that are green together.
_Avoid_: Stage, cycle step

## Demand and congestion

**Queue**:
The vehicles stopped or waiting on an Approach.
_Avoid_: Line, jam

**Pedestrian Demand**:
At least one pedestrian waiting at a Crosswalk for a Pedestrian Signal.
_Avoid_: Button press, waiting people

**Spillback**:
The road leading out of a Signal Site is so full that releasing more vehicles into it would block the Signal Site.
_Avoid_: Traffic jam, gridlock, overflow

**Congestion Level**:
A road segment's traffic state shown as one of three grades: free, slow or jammed.
_Avoid_: Traffic colour, jam level

## Decision making

**Controller**:
The decision maker that proposes the next Phase for every Signal Site: Fixed-time, Max-pressure or RL.
_Avoid_: AI, brain, agent

**Fixed-time Controller**:
The Controller that cycles Phases on a fixed schedule, as most of Ulaanbaatar does today; the Baseline every other Controller is compared against.
_Avoid_: Default, timer

**Max-pressure Controller**:
The Controller that gives green to the Phase whose waiting vehicles most exceed the vehicles already on their exit roads.
_Avoid_: Greedy, pressure AI

**RL Controller**:
The Controller whose choice of Phase is learned by reinforcement learning in the simulation.
_Avoid_: Neural, smart mode

**Safety Guard**:
The rule layer that approves, changes or overrides every Phase the Controller proposes; the only thing that changes signals.
_Avoid_: Rules engine, validator

**Override**:
A Safety Guard decision that replaces the Controller's proposal, always recorded with the rule that forced it.
_Avoid_: Correction, veto

**Wait Time**:
How long a Queue or a Pedestrian Demand has gone without green.
_Avoid_: Delay, red time

**Soft Cap**:
A Wait Time limit for an Approach that may be extended while the Approach's exit has Spillback.
_Avoid_: Max wait, timeout

**Hard Cap**:
A Wait Time limit that is never exceeded for any reason.
_Avoid_: Absolute max, safety timeout

## Demo

**Scenario**:
A named, repeatable traffic and pedestrian demand pattern, such as morning rush or incident.
_Avoid_: Test case, preset, mode

**Live Mode**:
Running a Scenario in real time on the map for people to watch and operate.
_Avoid_: Demo mode, realtime

**Experiment Mode**:
Running a Scenario as fast as possible without the map to compare Controllers.
_Avoid_: Benchmark, batch

**Operator**:
A person using the client to change the Controller, caps or Scenario, or to inject events.
_Avoid_: Admin, user

**Viewer**:
A person watching the client without changing anything.
_Avoid_: User, guest
