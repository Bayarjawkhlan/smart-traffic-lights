# smart-traffic-lights

## Vision service

`vision/` runs YOLO detection and tracking on recorded street video and shows what a camera would feed the Controller: the Queue on each Approach and the Pedestrian Demand at each Crosswalk, as an annotated MJPEG stream and a WebSocket of counts on port 8001. It is a separate showcase and does not drive the simulation. See [vision/README.md](vision/README.md).
