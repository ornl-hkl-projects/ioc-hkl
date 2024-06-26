#!../../bin/linux-x86_64/hklApp

< envPaths

# PYTHONPATH points to folders where Python modules are.
epicsEnvSet("PYTHONPATH","$(TOP)/python")

# Prefix set for Triple Axis Spectrometer -> TAS
epicsEnvSet("PREFIX", "HB3:")

cd ${TOP}

## Register all support components
dbLoadDatabase "${TOP}/dbd/hklApp.dbd"
hklApp_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords("db/hkl_main.db")

cd ${TOP}/iocBoot/${IOC}

pydev("import hklApp")
pydev("hkl_calc = hklApp.hklCalcs()")
#pydev("hkl_calc.test()")

iocInit

epicsThreadSleep(1)

#dbpf("$(PREFIX)wlen","1.54")
#dbpf("$(PREFIX)a","5.431")
#dbpf("$(PREFIX)b","5.431")
#dbpf("$(PREFIX)c","5.431")
#dbpf("$(PREFIX)alpha","90")
#dbpf("$(PREFIX)beta","90")
#dbpf("$(PREFIX)gamma","90")
#dbpf("$(PREFIX)omega","30")
#dbpf("$(PREFIX)chi","20")
#dbpf("$(PREFIX)phi","10")
#dbpf("$(PREFIX)tth","10")
#
#dbpf("$(PREFIX)h","1")
#dbpf("$(PREFIX)k","1")
#dbpf("$(PREFIX)l","1")

#dbl > pvlist.dbl

pydev("hkl_calc.test()")
