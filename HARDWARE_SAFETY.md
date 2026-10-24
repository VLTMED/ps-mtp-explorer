# Hardware Safety & Electrical Analysis

## Executive verdict

**PS MTP Explorer is electrically safe under normal operating conditions:** a healthy PS4 and phone, a compliant USB data cable, and adequate ventilation.

The app transfers files using standard USB Media Transfer Protocol (MTP) operations through Sony's USB APIs. The reviewed code contains no commands to raise USB voltage, disable electrical protections, or change cooling controls. The audit found **no credible mechanism by which normal use of the app would electrically damage the Southbridge or motherboard**.

This is a source-review conclusion, not a laboratory certification or a guarantee against faulty hardware. Damaged cables, shorts, liquid, defective accessories, and overheating remain real risks with any USB device. Electrical safety also does not guarantee software stability or protect against file loss.

## Myth vs. fact

### Myth 1: “A 33W, 67W, or 120W phone forces excessive power from the PS4.”

**Fact: A phone's fast-charging rating describes what it can accept from a compatible charger, not what it draws from every USB port.**

In a normal direct connection, the PS4 is the **source** supplying power and the phone is the **sink** receiving it. The phone's charging circuitry must follow the power available from the connection. It cannot make the PS4 generate a fast charger's higher voltage simply by requesting it. Fast charging requires compatible hardware and a supported charging protocol on both ends. [Qualcomm's charging FAQ](https://www.qualcomm.com/products/features/quick-charge/faq) explains this hardware dependency.

Ordinary USB data connections use nominal **5 V** power. Standard configured high-power budgets are **500 mA for USB 2.0** and **900 mA for single-lane SuperSpeed USB**. A USB 2.0 phone does not automatically get the SuperSpeed budget just because the port supports USB 3. These are USB protocol budgets, **not a measured PS4 current limit or an exact hardware cutoff**. Charging extensions can allow different currents; this audit did not establish their availability on every PS4 revision. See the [USB Type-C specification](https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf).

Expect ordinary USB charging rather than the phone's advertised fast-charge rate. Actual charging speed varies; the battery may charge slowly or lose charge if the phone itself uses more power than it receives.

### Myth 2: “The Southbridge burns out because the phone's charging current passes through it.”

**Fact: The USB data path and charging-power path serve different jobs.**

| Path | What it carries |
| :--- | :--- |
| USB data lines → USB controller and associated I/O circuitry | Electrical signals representing file data |
| Console power supply → USB power circuitry → VBUS and ground wires → phone | Power used by the phone |

The Southbridge handles I/O; it is not the series power path that carries the phone's normal charging current. USB host designs use separate power distribution and overcurrent protection, such as power switches or resettable fuses. The [USB motherboard power-design guide](https://www.usb.org/sites/default/files/power_delivery_motherboards.pdf) explains these arrangements.

The exact protection parts and thresholds on every PS4 board revision were not verified. Separate power and data paths also do not make the console immune to faults: a damaged connector or cable can short power onto a data line and damage the USB circuitry.

### Myth 3: “The app overrides USB voltage or disables safety limits.”

**Fact: The reviewed implementation requests file transfers, not electrical changes.**

Its USB code discovers devices, reads descriptors, opens and claims an MTP interface, and exchanges control and bulk transfers. Its recovery reset targets the MTP interface; it is not a voltage change or a physical power cycle.

The review found no voltage-control commands, charging-protocol negotiation, power-role switching, fan-curve changes, or writes to motherboard power-control registers. These conclusions come from reviewing the USB adapter (`src/ps4/usb_ps4.c`), interface selection (`src/usb_select.c`), MTP implementation (`src/mtp.c`), and privileged-access code.

Homebrew can have elevated privileges, so this finding describes **what this code does**. It is not a claim that all privileged software is incapable of affecting hardware.

### Myth 4: “A 50 GB or larger transfer electrically overloads the port.”

**Fact: A larger file mainly means the same kind of USB activity continues for longer.**

USB data uses electrical signals with levels controlled by the USB hardware. Sending more bytes does not increase the signal voltage or request more charging voltage. File size alone does not establish an electrical overload.

Sustained transfers keep the USB circuitry, processor, storage, and phone active, producing normal operating heat, much like other sustained USB storage activity. The audit found no special electrical overload mechanism caused by large MTP transfers. Temperatures were not measured, so this does not promise a particular thermal margin on an aging, dusty, damaged, or poorly ventilated console.

## Practical tips

- Use a compliant, undamaged **USB data cable**. Replace cables with frayed insulation, loose plugs, or bent contacts.
- Keep the PS4's vents clean and unobstructed, with space for airflow.
- Avoid non-standard USB splitters, faulty OTG adapters, and Y-cables that connect a charger and the PS4 to the same power line. Poorly designed powered hubs can also feed power back toward the console.
- Do not keep using a port or cable that becomes unusually hot, smells burnt, or shows visible damage. Follow [Sony's PS4 safety guidance](https://www.playstation.com/content/dam/global_pdc/en/corporate/support/manuals/ps4-docs/2200/CUH-22XXA_PS4_Safety_Guide_Web%24en.pdf).
- Keep the phone connected until a transfer finishes to reduce the chance of incomplete files.

## What the audit establishes

The hardware review assessed the local source and USB power standards. It did not measure console current, voltage, temperature, protection-trip thresholds, or behavior under electrical faults, and it did not verify every PS4 motherboard revision or every released binary.

**Normal MTP use with sound hardware presents no identified app-specific electrical danger. A phone's fast-charging rating and a file's size are not evidence that the app can burn out a PS4.**
