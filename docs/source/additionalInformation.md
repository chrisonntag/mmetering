## Additional information <a name="additional"></a>

### Talking Modbus using the minimalmodbus library
- functioncode 4: read Input Registers
- functioncode 3: read Holding Registers
- functioncode 16: write multiple Registers (Holding)

#### Examples

```python
ImportWh = instrument.read_float(int('0x48', 16), functioncode=4, numberOfRegisters=2)
```

## Appendix <a name="appendix"></a>

### Eastron SDM630
#### Input Registers

| Description                       | Units      | Hex | # of Registers |
|-----------------------------------|------------|-----|----------------|
| Phase 1 line to neutral volts.    | Volts      | 00  | 2              |
| Phase 2 line to neutral volts.    | Volts      | 02  | 2              |
| Phase 3 line to neutral volts.    | Volts      | 04  | 2              |
| Phase 1 current.                  | Amps       | 06  | 2              |
| Phase 2 current.                  | Amps       | 08  | 2              |
| Phase 3 current.                  | Amps       | 0A  | 2              |
| Phase 1 power.                    | Watts      | 0C  | 2              |
| Phase 2 power.                    | Watts      | 0E  | 2              |
| Phase 3 power.                    | Watts      | 10  | 2              |
| Frequency of supply voltages.     | Hz         | 46  | 2              |
| Import Wh since last reset (2).   | kWh/MWh    | 48  | 2              |
| Export Wh since last reset (2).   | kWh/MWh    | 4A  | 2              |
| Import VArh since last reset (2). | kVArh      | 4C  | 2              |
| Export VArh since last reset (2). | kVArh      | 4E  | 2              |
| VAh since last reset (2).         | kVAh/ MVAh | 50  | 2              |

---

#### Holding Registers

| Address | Parameter         | Hex | # of Registers | Valid Range                                                                                                                                                                               | Mode |
|---------|-------------------|-----|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------|
| 40025   | Password          | 18  | 4              | Write password for access to protected registers. Read zero. Reading will also reset the password timeout back to one minute. Default password is 0000.                                   | r/w  |
| 40029   | Network Baud Rate | 1C  | 2              | Write the network port baud rate for MODBUS Protocol, where: 0 = 2400 baud. 1 = 4800 baud. 2 = 9600 baud, default.,3 = 19200 baud. 4 = 38400 baud. Requires a restart to become effective | r/w  |
| 40043   | Serial Number Hi  | 2A  | 2              | Read the first product serial number.                                                                                                                                                     | ro   |
| 40045   | Serial Number Lo  | 2C  | ?              | Read the second product serial number.                                                                                                                                                    | ro   |



