# mmetering-server [![Build Status](http://ci.mmetering.chrisonntag.com/job/mmetering-server/badge/icon)](http://ci.mmetering.chrisonntag.com/job/mmetering-server)

MMetering is a smart metering software built on Django and Celery.

## Table of Contents

1. [Install](#install)
2. [Setup](#setup)
3. [Additional Information](#additional)
4. [Appendix](#appendix)
5. [References](#references)

## Install <a name="install"></a>

Clone this repository into the home folder of the target system with
```git clone https://github.com/chrisonntag/mmetering-server.git mmetering-server```.
If you want to install further apps, clone them into the project folder as well.

Rename ```my.sample.cnf``` to ```my.cnf``` and fill out all necessary values. 
Due to the fact, that Linux assigns port names in the order they respond on the bus, the exact port 
name can change. Therefore, MMetering uses a symlink created per device in ```/dev/serial/by-id/```.
This folder is mounted into the docker container (see ```docker-compose.yml```). Use the whole 
path of the device for the modbus-port value, for example

```
/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A50285BI-if00-port0
```

Leave the client section blank until
the database credentials will be set in the ```mysql_conf.txt``` file.

Rename ```docker-compose-sample.yml``` to ```docker-compose.yml``` and follow possible instructions of
aditionally added plugins/apps.

Rename ```mysql_sample_conf.txt``` to ```mysql_conf.txt``` and use the same values as in the ```my.cnf``` file.
Docker will use these credentials for the setup process of the mysql container. Check that the host entered
in the ```my.cnf``` file is the same name as the mysql service in the docker-compose file!

Rename ```production-sample.py``` in ```mmetering_server/settings/``` to ```production.py``` and add all
downloaded apps to the ```INSTALLED_APPS``` list.
Furthermore, add possibly wanted domains and the ```localhost``` to ```ALLOWED_DOMAINS```.
In order to receive mails from the mmetering system if errors occur, add yourself to ```ADMIN``` and/or
```MANAGERS```. Errors and Exceptions will be sent to ```ADMINS```, all other system mails to ```MANAGERS```.

In order to let mmetering-server run under an own alias like ```mmetering```, add 

```bash
127.0.0.1   mmetering
```

to your ```/etc/hosts``` file and add ```mmetering``` to your ```ALLOWED_DOMAINS```.

Check your docker and docker-compose version:

```bash
docker >= 18.06.1
docker-compose >= 1.22.0
```

Run ```docker-compose build``` in order to build all necessary images. Verify that at least
```mmetering_server_web```, ```mmetering_server_celery``` and ```mmetering_server_celery-beat``` have
been built with

```bash
docker images
```

Finally, fire up all containers with

```bash
docker-compose up
```

## Setup <a name="setup"></a>

### Add user

Beside your admin account, which you create on the console with
```python3 manage.py createsuperuser```
you need to create two more user profiles in the admin backend. The first one has only the permission
to view the live data on the dashboard. The second one can also create flats and meters and can download
the whole data.

Log into the admin backend, click on Users -> Add User and create both users. After that, edit each of them
and add the desired permissions.

Note: Both users need to have staff status in order to be able to login at all.

### Add flats and meters

Log into the admin backend with either the admin or the service provider account. Follow all instructions.


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


## References <a name="references"></a>

This software is using the wonderful [Gentelella Theme](https://github.com/puikinsh/gentelella).
