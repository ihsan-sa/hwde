# P2 digest (usb-buck)
5 blocks / 3 sheets (usb, power, mcu) + thin root, ~28 parts. JLC04161H-3313
4L standard; In1 GND, In2 +3V3. 40x30 target (55x45 cap). Nets contractual:
bare VBUS/+3V3/GND global, /USB_DP //USB_DM root-labeled, others /<sheet>/N.
All research OPENs settled (buck, 1k LED, hardwired 1.5k, no VBUS sense,
shell direct, 10uF VBUS ceiling). ~$62-75/10. H1 AUTO-approved.
Re-opens at P3: TVS VBUS clamp pin; crystal CL -> load caps; Basic/Extended.
