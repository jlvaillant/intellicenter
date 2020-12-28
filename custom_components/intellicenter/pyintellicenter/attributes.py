"""Definition of all the attributes per OBJTYP."""

USER_PRIVILEGES = {
    "p": "Pool Access",
    "P": "Pool temperature",
    "h": "Pool Heat Mode",
    "m": "Spa Access",
    "S": "Spa Temperature",
    "n": "Spa Heat Mode",
    "e": "Schedule Access",
    "v": "Vacation Mode",
    "f": "Features Access",
    "l": "Lights Access",
    "c": "Chemistry Access",
    "u": "Usage Access",
    "C": "System Configuration",
    "o": "Support",
    "q": "Alerts and Notifications",
    "i": "User Portal",
    "k": "Groups",
    "a": "Advanced Settings",
    "t": "Status",
    "x": "Service Mode Circuits",
    "g": "General Settings",
}

# represents a body of water (pool or spa)
BODY_ATTRIBUTES = {
    "ACT1",  # (int) ???
    "ACT2",  # (int) ???
    "ACT3",  # (int) ???
    "ACT4",  # (int) ???
    "HEATER",  # (objnam)
    "HITMP",  # (int) maximum temperature to set
    "HNAME",  # equals to OBJNAM
    "HTMODE",  # (int) 1 if currently heating, 0 if not
    "HTSRC",  # (objnam) the heating source (or '00000')
    "LISTORD",  # (int) used to order in UI
    "LOTMP",  # (int) desired temperature
    "LSTTMP",  # (int) last recorded temperature
    "MANHT",  # Manual heating ???
    "MANUAL",  # (int) ???
    "PARENT",  # (objnam) parent object
    "PRIM",  # (int) ???
    "READY",  # (ON/OFF) ???
    "SEC",  # (int) ???
    "SETPT",  # (int) set point (same as 'LOTMP' AFAIK)
    "SHARE",  # (objnam) sharing with that other body?
    "SNAME",  # (str) friendly name
    "STATIC",  # (ON/OFF) 'OFF'
    "STATUS",  # (ON/OFF) 'ON' is body is "active"
    "SUBTYP",  # 'POOL' or 'SPA'
    "VOL",  # (int) Volume in Gallons
}

CIRCGRP_ATTRIBUTES = {"ACT", "CIRCUIT", "DLY", "LISTORD", "PARENT", "READY", "STATIC"}

CIRCUIT_ATTRIBUTES = {
    "ACT",  # to be set for changing USE attribute
    "BODY",
    "CHILD",
    "COVER",
    "DNTSTP",  # (ON/OFF) "Don't Stop", disable egg timer
    "FEATR",  # (ON/OFF) Featured
    "FREEZE",  # (ON/OFF) Freeze Protection
    "HNAME",  # equals to OBJNAM
    "LIMIT",
    "LISTORD",  # (int) used to order in UI
    "OBJLIST",
    "PARENT",  # OBJNAM of the parent object
    "READY",  # (ON/OFF) ??
    "SELECT",  # ???
    "SET",  # (ON/OFF) for light groups only
    "SHOMNU",  # (str) permissions
    "SNAME",  # (str) friendly name
    "STATIC",  # (ON/OFF) ??
    "STATUS",  # (ON/OFF) 'ON' if circuit is active
    "SUBTYP",  # subtype can be '?
    "SWIM",  # (ON/OFF) for light groups only
    "SYNC",  # (ON/OFF) for light groups only
    "TIME",  # (int) Egg Timer, number of minutes
    "USAGE",
    "USE",  # for lights with light effects, indicate the 'color'
}

# represents External Equipment like covers
EXTINSTR_ATRIBUTES = {
    "BODY",  # (objnam) which body it covers
    "HNAME",  # equals to OBJNAM
    "LISTORD",  # (int) used to order in UI
    "NORMAL",  # (ON/OFF) 'ON' for Cover State Normally On
    "PARENT",  # (objnam)
    "READY",  # (ON/OFF) ???
    "SNAME",  # (str) friendly name
    "STATIC",  # (ON/OFF) 'OFF'
    "STATUS",  # (ON/OFF) 'ON' if cover enabled
    "SUBTYP",  # only seen 'COVER'
}

# no idea what this represents
FEATR_ATTRIBUTES = {"HNAME", "LISTORD", "READY", "SNAME", "SOURCE", "STATIC"}

HEATER_ATTRIBUTES = {
    "BODY",  # the objnam of the body the pump serves or a list (separated by a space)
    "BOOST",  # (int) ??
    "COMUART",  # X25 related?
    "COOL",  # (ON/OFF)
    "DLY",  # (int) ??
    "HNAME",  # equals to OBJNAM
    "HTMODE",  # (int) ??
    "LISTORD",  # (int) used to order in UI
    "PARENT",  # (objnam) parent (module) for this heater
    "READY",  # (ON/OFF)
    "SHOMNU",  # (str) permissions
    "SNAME",  # (str) friendly name
    "START",  # (int) ??
    "STATIC",  # (ON/OFF) 'OFF'
    "STATUS",  # (ON/OFF) only seen 'ON'
    "STOP",  # (int) ??
    "SUBTYP",  # type of heater 'GENERIC','SOLAR','ULTRA','HEATER'
    "TIME",  # (int) ??
}

MODULE_ATTRUBUTES = {
    "CIRCUITS",  # [ objects ] the objects that the module controls
    "PARENT",  # (objnam) the parent (PANEL) of the module
    "PORT",  # (int) no idea
    "SNAME",  # friendly name
    "STATIC",  # (ON/OFF) 'ON'
    "SUBTYP",  # type of the module (like 'I5P' or 'I8PS')
    "VER",  # (str) the version of the firmware for this module
}

PANEL_ATTRIBUTES = {
    "HNAME",  # equals to OBJNAM
    "LISTORD",  # (int) used to order in UI
    "OBJLIST",  # [ (objnam) ] the elements managed by the panel
    "PANID",  # ??? only seen 'SHARE'
    "SNAME",  # friendly name
    "STATIC",  # only seen 'ON'
    "SUBTYP",  # only seen 'OCP'
}

# represent a USER for the system
PERMIT_ATTRIBUTES = {
    "ENABLE",  # (ON/OFF) ON if user is enabled
    "PASSWRD",  # 4 digit code or ''
    "SHOMNU",  # privileges associated with this user
    "SNAME",  # friendly name
    "STATIC",  # (ON/OFF) only seen ON
    "SUBTYP",  # ADV for administrator, BASIC for guest
    "TIMOUT",  # (int) in minutes, timeout for user session
}

# represents a PUMP setting
PMPCIRC_ATTRIBUTES = {
    "BODY",  # not sure, I've only see '00000'
    "CIRCUIT",  # (objnam) the circuit this setting is for
    "GPM",  # (int): the flow setting for the pump if select is GPM
    "LISTORD",  # (int) used to order in UI
    "PARENT",  # (objnam) the pump the setting belongs to
    "SPEED",  # (int): the speed setting for the pump if select is RPM
    "SELECT",  # 'RPM' or 'GPM'
}

# no idea what this object type represents
# only seem to be one instance of it
PRESS_ATTRIBUTES = {
    "SHOMNU",  # (ON/OFF) ???
    "SNAME",  # seems equal to objnam
    "STATIC",  # (ON/OFF) only seen ON
}

# represents a PUMP
PUMP_ATTRIBUTES = {
    "BODY",  # the objnam of the body the pump serves or a list (separated by a space)
    "CIRCUIT",  # (int) ??? only seen 1
    "COMUART",  # X25 related?
    "HNAME",  # same as objnam
    "GPM",  # (int) when applicable, real time Gallon Per Minute
    "LISTORD",  # (int) used to order in UI
    "MAX",  # (int) maximum RPM
    "MAXF",  # (int) maximum GPM (if applicable, 0 otherwise)
    "MIN",  # (int) minimum RPM
    "MINF",  # (int) minimum GPM (if applicable, 0 otherwise)
    "NAME",  # seems to equal OBJNAM
    "OBJLIST",  # ([ objnam] ) a list of PMPCIRC settings
    "PRIMFLO",  # (int) Priming Speed
    "PRIMTIM",  # (int) Priming Time in minutes
    "PRIOR",  # (int) ???
    "PWR",  # (int) when applicable, real time Power usage in Watts
    "RPM",  # (int) when applicable, real time Rotation Per Minute
    "SETTMP",  # (int) Step size for RPM
    "SETTMPNC",  # (int) ???
    "SNAME",  # friendly name
    "STATUS",  # only seen 10 for on, 4 for off
    "SUBTYP",  # type of pump: 'SPEED' (variable speed), 'FLOW' (variable flow), 'VSF' (both)
    "SYSTIM",  # (int) ???
}


# represents a mapping between a remote button and a circuit
REMBTN_ATTRIBUTES = {
    "CIRCUIT",  # (objnam) the circuit triggered by the button
    "LISTORD",  # (int) which button on the remote (1 to 4)
    "PARENT"  # (objnam) the remote this button is associated with
    "STATIC",  # (ON/OFF) not sure, only seen 'ON'
}

# represents a REMOTE
REMOTE_ATTRIBUTES = {
    "BODY",  # (objnam) the body the remote controls
    "COMUART",  # X25 address?
    "ENABLE",  # (ON/OFF) 'ON' if the remote is set to active
    "HNAME",  # same as objnam
    "LISTORD",  # number likely used to order things in UI
    "SNAME",  # friendly name
    "STATIC",  # (ON/OFF) not sure, only seen 'OFF'
    "SUBTYP",  # type of the remote, I've only seen IS4
}

# represents a SCHEDULE
SCHED_ATTRIBUTES = {
    "ACT",
    "CIRCUIT",  # (objnam) the circuit controlled by this schedule
    "DAY",  # the days this schedule run (example: 'MTWRFAU' for every day, 'AU' for weekends)
    "DNTSTP",  # 'ON' or 'OFF" means Don't Stop. Set to ON to never end...
    "HEATER",  # set to a HEATER objnam is the schedule should trigger heating, '00000' for off, '00001' for Don't Change
    "HNAME",  # same as objnam
    "HITMP",  # number but not sure
    "LISTORD",  # number likely used to order things in UI
    "LOTMP",  # number. when heater is set, that is the desired temperature
    "SINGLE",  # 'ON' if the schedule is not to repeat
    "SNAME",  # the friendly name of the schedule
    "START",  # start time mode
    # 'ABSTIM' means absolute and 'TIME' will be the startime
    # 'SRIS' means Sunrise, 'SSET' means Sunset
    "STATIC",  # (ON/OFF) not sure, only seen 'OFF'
    "STATUS",  # 'ON' if schedule is active, 'OFF' otherwise
    "STOP",  # stop time mode ('ABSTIME','SRIS' or 'SSET')
    "TIME",  # time the schedule starts in 'HH,MM,SS' format (24h clock)
    "TIMOUT",  # time the schedule stops in 'HH,MM,SS' format (24h clock)
    "VACFLO",  # ON/OFF not sure of the meaning...
}

# represents a SENSOR
SENSE_ATTRIBUTES = {
    "CALIB",  # (int) calibration value
    "HNAME",  # same as objnam
    "LISTORD",  # number likely used to order things in UI
    "MODE",  # I've only seen 'OFF' so far
    "NAME",  # I've only seen '00000'
    "PARENT",  # the parent's objnam
    "PROBE",  # the uncalibrated reading of the sensor
    "SNAME",  # friendly name
    "SOURCE",  # the calibrated reading of the sensor
    "STATIC",  # (ON/OFF) not sure, only seen 'ON'
    "STATUS",  # I've only seen 'OK' so far
    "SUBTYP",  # 'SOLAR','POOL' (for water), 'AIR'
}

# represent the (unique instance of) SYSTEM object
SYSTEM_ATTRIBUTES = [
    "ACT",  # ON/OFF but not sure what it does
    "ADDRESS",  # Pool Address
    "AVAIL",  # ON/OFF but not sure what it does
    "CITY",  # Pool City
    "COUNTRY",  # Country obviously (example 'United States')
    "EMAIL",  # primary email for the owner
    "EMAIL2",  # secondary email for the owner
    "HEATING",  # ON/OFF: Pump On During Heater Cool-Down Delay
    "HNAME",  # same as objnam
    "LOCX",  # (float) longitude
    "LOCY",  # (float) latitude
    "MANHT",  # ON/OFF: Manual Heat
    "MODE",  # unit system, 'METRIC' or 'ENGLISH'
    "NAME",  # name of the owner
    "PASSWRD",  # a 4 digit password or ''
    "PHONE",  # primary phone number for the owner
    "PHONE2",  # secondary phone number for the owner
    "PROPNAME",  # name of the property
    "SERVICE",  # 'AUTO' for automatic
    "SNAME",  # a crazy looking string I assume to be unique to this system
    "START",  # almost looks like a date but no idea
    "STATE",  # Pool State
    "STATUS",  # ON/OFF
    "STOP",  # same value as START
    "TEMPNC",  # ON/OFF
    "TIMZON",  # (int) Time Zone (example '-8' for US Pacific)
    "VACFLO",  # ON/OFF, vacation mode
    "VACTIM",  # ON/OFF
    "VALVE",  # ON/OFF: Pump Off During Valve Action
    "VER",  # (str) software version
    "ZIP",  # Pool Zip Code
]

# represents the system CLOCK
# note that there are 2 clocks in the system
# one only contains the SOURCE attribute
# the other everything but SOURCE
SYSTIM_ATTRIBUTES = {
    "CLK24A",  # clock mode, 'AMPM' or 'HR24'
    "DAY",  # in 'MM,DD,YY' format
    "DLSTIM",  # ON/OFF, ON for following DST
    "HNAME",  # same as objnam
    "LOCX",  # (float) longitude
    "LOCY",  # (float) latitude
    "MIN",  # in 'HH,MM,SS' format (24h clock)
    "SNAME",  # unused really, likely equals to OBJNAM
    "SOURCE",  # set to URL if time is from the internet
    "STATIC",  # (ON/OFF) not sure, only seen 'ON'
    "TIMZON",  # (int) timezone (example '-8' for US Pacific)
    "ZIP",  # ZipCode
}

VALVE_ATTRIBUTES = {
    "ASSIGN",  # 'NONE', 'INTAKE' or 'RETURN'
    "CIRCUIT",  # I've only seen '00000'
    "DLY",  # (ON/OFF)
    "HNAME",  # same as objnam
    "PARENT",  # (objnam) parent (a module)
    "SNAME",  # friendly name
    "STATIC",  # (ON/OFF) I've only seen 'OFF'
    "SUBTYP",  # I've only seen 'LEGACY'
}

ALL_ATTRIBUTES_BY_TYPE = {
    "BODY": BODY_ATTRIBUTES,
    "CIRCGRP": CIRCGRP_ATTRIBUTES,
    "CIRCUIT": CIRCUIT_ATTRIBUTES,
    "EXTINSTR": EXTINSTR_ATRIBUTES,
    "FEATR": FEATR_ATTRIBUTES,
    "HEATER": HEATER_ATTRIBUTES,
    "MODULE": MODULE_ATTRUBUTES,
    "PANEL": PANEL_ATTRIBUTES,
    "PMPCIRC": PMPCIRC_ATTRIBUTES,
    "PRESS": PRESS_ATTRIBUTES,
    "PUMP": PUMP_ATTRIBUTES,
    "REMBTN": REMBTN_ATTRIBUTES,
    "REMOTE": REMOTE_ATTRIBUTES,
    "SCHED": SCHED_ATTRIBUTES,
    "SENSE": SENSE_ATTRIBUTES,
    "SYSTEM": SYSTEM_ATTRIBUTES,
    "SYSTIM": SYSTIM_ATTRIBUTES,
    "VALVE": VALVE_ATTRIBUTES,
}
