# ADC Type-1 FW Regression Test Suite

## Overview

The ADC Type-1 Regression Test Suite is based on the pytest framework (https://docs.pytest.org/en/latest/contents.html)
and the pytest-bdd extension (https://github.com/pytest-dev/pytest-bdd)

## Requirements

### Testbed
A testbed with the following configuration:

### Raspbian Firmware 

- Python3 should be available by default
- Pipenv needs to be installed
  
  To install run 
  ```shell script
  $ sudo apt install pipenv
  ``` 
  Note: here are some tips for working with pipenv on Raspberry Pis: 
  https://blog.y-modify.org/en/2018/07/31/pipenv-raspi-tips/

## Execution

### Preparation

In order to configure the python environment first run.
```shell script
$ pipenv install
```

The test-bench requires access to the SPI pins in order to drive the relay on the PiFace2 hat.
Am install script is supplied with the PiFace driver package which is installed when executing the previous commmand.
To install the SPI driver run the following commands once pipenv install had completed successfully:

```shell script
$ pipenv shell
$ sudo pifaceio-install-spidev.sh
```

### Running a full regression

To execute a full regression test simply run

```shell script
$ pipenv run pytest --adc_ip_addr=10.2.3.100 --cmc_ip_addr=10.2.3.1002
```

The options --adc_ip_address as well as --cmc_ip_addr are mandatory

### Running without JLink

This mode of execution is typically used for debugging in which case the JLink is driven by the development PC.

```shell script
$ pytest --adc_ip_addr=10.250.2.225 --cmc_ip_addr=10.250.11.40 --no_jlink
```

### Running a specific Feature only

_Note that the IP address options will be omitted in teh following examples_

```shell script
$ pipenv run pytest ./steps/<step definition file>
```

### Running tests based on tags

_Note that the IP address options will be omitted in teh following examples_

To execute all scenarios marked with '@smoke_test' run

```shell script
$ pipenv run py.test -m "smoketest"
```

To execute all scenarios marked with '@release_test' run 

```shell script
$ pipenv run py.test -m "release_test"
```

To execute all scenarios marked with '@release_test' and all scenarios marked
with '@smoke_test' run 

```shell script
$ pipenv run py.test -m "release_test and smoke_test"
```

