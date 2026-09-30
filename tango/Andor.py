############################################################################
# This file is part of LImA, a Library for Image Acquisition
#
# Copyright (C) : 2009-2026
# European Synchrotron Radiation Facility
# BP 220, Grenoble 38043
# FRANCE
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
############################################################################
#=============================================================================
#
# file :        Andor.py
#
# description : Python source for the Andor and its commands.
#                The class is derived from Device. It represents the
#                CORBA servant object which will be accessed from the
#                network. All commands which can be executed on the
#                Pilatus are implemented in this file.
#
# project :     TANGO Device Server
#
# copyleft :    European Synchrotron Radiation Facility
#               BP 220, Grenoble 38043
#               FRANCE
#
#=============================================================================
#         (c) - Bliss - ESRF
#=============================================================================
#
import tango
from tango import AttrWriteType, DevState
from tango.server import Device, attribute, command, device_property

from lima import core
from Lima import Andor as AndorAcq
from lima.server import AttrHelper


def _make_dynamic_enum_fget_fset(attr_name, dict_attr_name, target_attr="_AndorInterface"):
    """Like AttrHelper.make_fget_fset, but the enum dict isn't a fixed
    class-level constant: p_gain/vs_speed/adc_speed/fan_mode/high_capacity/
    baseline_clamp's valid values (and, for the last three, whether the
    attribute is supported at all) are queried from the actual connected
    camera at init_device time and stored per-instance.
    """
    camel = AttrHelper._title_case(attr_name)
    get_name, set_name = "get" + camel, "set" + camel

    def fget(self):
        target = getattr(self, target_attr)
        value = getattr(target, get_name)()
        return AttrHelper.getDictKey(getattr(self, dict_attr_name), value)

    def fset(self, value):
        d = getattr(self, dict_attr_name)
        resolved = AttrHelper.getDictValue(d, value.upper())
        if resolved is None:
            tango.Except.throw_exception(
                "WrongData", "Wrong value %s: %s" % (attr_name, value.upper()), "LimaCCDs Class"
            )
        target = getattr(self, target_attr)
        getattr(target, set_name)(resolved)

    return fget, fset


class Andor(Device):

    core.DEB_CLASS(core.DebModule.DebModApplication, 'LimaCCDs')

    # ------------------------------------------------------------------
    #    Static properties
    # ------------------------------------------------------------------
    _AndorCamera = None
    """Reference to Lima andor camera binding"""
    _AndorInterface = None
    """Reference to Lima andor interface binding"""

    _FastExtTrigger = {'ON': True, 'OFF': False}
    _Cooler = {'ON': True, 'OFF': False}
    _ShutterLevel = {'LOW': 0, 'HIGH': 1}

    # ------------------------------------------------------------------
    #    Device properties (initial hardware configuration only - the
    #    live attributes of the same name below read/write the camera
    #    directly, they don't share storage with these)
    # ------------------------------------------------------------------
    config_path = device_property(dtype=str, default_value="")
    serial_number = device_property(dtype=int, default_value=0)
    p_gain = device_property(dtype=str, default_value="")
    vs_speed = device_property(dtype=str, default_value="")
    adc_speed = device_property(dtype=str, default_value="")
    temperature_sp = device_property(dtype=int, default_value=0)
    cooler = device_property(dtype=str, default_value="")
    fast_ext_trigger = device_property(dtype=str, default_value="")
    shutter_level = device_property(dtype=str, default_value="")
    fan_mode = device_property(dtype=str, default_value="")
    high_capacity = device_property(dtype=str, default_value="")
    baseline_clamp = device_property(dtype=str, default_value="")

    # ------------------------------------------------------------------
    #    Device initialization
    # ------------------------------------------------------------------
    @core.DEB_MEMBER_FUNCT
    def init_device(self):
        Device.init_device(self)

        if self._AndorInterface.getFanMode() == AndorAcq.FAN_UNSUPPORTED:
            self._fan_mode_dict = {'UNSUPPORTED': AndorAcq.FAN_UNSUPPORTED}
        else:
            self._fan_mode_dict = {
                'FULL': AndorAcq.FAN_ON_FULL,
                'LOW': AndorAcq.FAN_ON_LOW,
                'OFF': AndorAcq.FAN_OFF,
            }

        if self._AndorInterface.getHighCapacity() == AndorAcq.HC_UNSUPPORTED:
            self._high_capacity_dict = {'UNSUPPORTED': AndorAcq.HC_UNSUPPORTED}
        else:
            self._high_capacity_dict = {
                'HIGH_CAPACITY': AndorAcq.HIGH_CAPACITY,
                'HIGH_SENSITIVITY': AndorAcq.HIGH_SENSITIVITY,
            }

        if self._AndorInterface.getBaselineClamp() == AndorAcq.BLCLAMP_UNSUPPORTED:
            self._baseline_clamp_dict = {'UNSUPPORTED': AndorAcq.BLCLAMP_UNSUPPORTED}
        else:
            self._baseline_clamp_dict = {
                'ON': AndorAcq.BLCLAMP_ENABLED,
                'OFF': AndorAcq.BLCLAMP_DISABLED,
            }

        # prepare lists of supported PGain/VerticalShiftSpeed/AdcSpeed
        self._p_gain_dict = {}
        for ind in range(self._AndorInterface.getPGainMaxIndex()):
            self._p_gain_dict[self._AndorInterface.getPGainString(ind)] = ind

        self._vs_speed_dict = {}
        for ind in range(self._AndorInterface.getVsSpeedMaxIndex()):
            self._vs_speed_dict[self._AndorInterface.getVsSpeedString(ind)] = ind

        self._adc_speed_dict = {}
        for ind in range(self._AndorInterface.getAdcSpeedMaxIndex()):
            self._adc_speed_dict[self._AndorInterface.getAdcSpeedPaireString(ind)] = ind

        # Leagcy code used by AttrHelper.get_attr_string_value_list
        self.__FastExtTrigger = self._FastExtTrigger
        self.__Cooler = self._Cooler
        self.__ShutterLevel = self._ShutterLevel
        self.__FanMode = self._fan_mode_dict
        self.__HighCapacity = self._high_capacity_dict
        self.__BaselineClamp = self._baseline_clamp_dict
        self.__PGain = self._p_gain_dict
        self.__VsSpeed = self._vs_speed_dict
        self.__AdcSpeed = self._adc_speed_dict

        # Apply properties if any
        if self.p_gain:
            self._AndorInterface.setPGain(self._p_gain_dict[self.p_gain])

        if self.vs_speed:
            self._AndorInterface.setVsSpeed(self._vs_speed_dict[self.vs_speed])

        if self.adc_speed:
            self._AndorInterface.setAdcSpeed(self._adc_speed_dict[self.adc_speed])

        if self.temperature_sp:
            self._AndorInterface.setTemperatureSP(self.temperature_sp)

        if self.cooler:
            self._AndorInterface.setCooler(self._Cooler[self.cooler])

        if self.fast_ext_trigger:
            self._AndorInterface.setFastExtTrigger(self._FastExtTrigger[self.fast_ext_trigger])

        if self.shutter_level:
            self._AndorInterface.setShutterLevel(self._ShutterLevel[self.shutter_level])

        if 'UNSUPPORTED' in self._fan_mode_dict and self.fan_mode:
            deb.Error('Cannot set fan_mode property, not supported for this camera model')
        elif self.fan_mode:
            self._AndorInterface.setFanMode(self._fan_mode_dict[self.fan_mode])

        if 'UNSUPPORTED' in self._high_capacity_dict and self.high_capacity:
            deb.Error('Cannot set high_capacity property, not supported for this camera model')
        elif self.high_capacity:
            self._AndorInterface.setHighCapacity(self._high_capacity_dict[self.high_capacity])

        if 'UNSUPPORTED' in self._baseline_clamp_dict and self.baseline_clamp:
            deb.Error('Cannot set baseline_clamp propery, not supported for this camera model')
        elif self.baseline_clamp:
            self._AndorInterface.setBaselineClamp(self._baseline_clamp_dict[self.baseline_clamp])

        self.set_state(DevState.ON)

    # ------------------------------------------------------------------
    #    Commands
    # ------------------------------------------------------------------
    @command(dtype_in=str, dtype_out=(str,))
    @core.DEB_MEMBER_FUNCT
    def getAttrStringValueList(self, attr_name):
        return AttrHelper.get_attr_string_value_list(self, attr_name)

    # ------------------------------------------------------------------
    #    Attributes with custom read logic
    # ------------------------------------------------------------------
    def _timing_fget(self):
        return [self._AndorCamera.getExpTime(), self._AndorCamera.getLatTime()]

    timing = attribute(
        dtype=(float,),
        max_dim_x=2,
        access=AttrWriteType.READ,
        unit="second",
        format="%f",
        doc="[0]: exposure, [1]: latency",
        fget=_timing_fget,
    )

    # ------------------------------------------------------------------
    #    Attributes with a per-instance (hardware-queried) enum
    # ------------------------------------------------------------------
    _p_gain_fget, _p_gain_fset = _make_dynamic_enum_fget_fset("p_gain", "_p_gain_dict")
    p_gain_attr = attribute(
        name="p_gain",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        format="%s",
        doc="Preamplifier gain from X1 to Xn (see detector spec.)",
        fget=_p_gain_fget,
        fset=_p_gain_fset,
    )

    _vs_speed_fget, _vs_speed_fset = _make_dynamic_enum_fget_fset("vs_speed", "_vs_speed_dict")
    vs_speed_attr = attribute(
        name="vs_speed",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="The vertical shift speed, in us/pixel",
        fget=_vs_speed_fget,
        fset=_vs_speed_fset,
    )

    _adc_speed_fget, _adc_speed_fset = _make_dynamic_enum_fget_fset("adc_speed", "_adc_speed_dict")
    adc_speed_attr = attribute(
        name="adc_speed",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="The ADC and Horizontal shift speed, in ADCchannel/Freq.Mhz",
        fget=_adc_speed_fget,
        fset=_adc_speed_fset,
    )

    _fan_mode_fget, _fan_mode_fset = _make_dynamic_enum_fget_fset("fan_mode", "_fan_mode_dict")
    fan_mode_attr = attribute(
        name="fan_mode",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="The FAN mode for extra-cooling: FAN_OFF, FAN_ON_FULL or FAN_ON_LOW "
        "(UNSUPPORTED on some camera models)",
        fget=_fan_mode_fget,
        fset=_fan_mode_fset,
    )

    _high_capacity_fget, _high_capacity_fset = _make_dynamic_enum_fget_fset(
        "high_capacity", "_high_capacity_dict"
    )
    high_capacity_attr = attribute(
        name="high_capacity",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="HIGH_CAPACITY or HIGH_SENSITIVITY (UNSUPPORTED on some camera models)",
        fget=_high_capacity_fget,
        fset=_high_capacity_fset,
    )

    _baseline_clamp_fget, _baseline_clamp_fset = _make_dynamic_enum_fget_fset(
        "baseline_clamp", "_baseline_clamp_dict"
    )
    baseline_clamp_attr = attribute(
        name="baseline_clamp",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="The baseline clamping for threshold: ON or OFF (UNSUPPORTED on some camera models)",
        fget=_baseline_clamp_fget,
        fset=_baseline_clamp_fset,
    )

    # ------------------------------------------------------------------
    #    Attributes fully dispatched by naming convention (fixed enums,
    #    or no enum at all)
    # ------------------------------------------------------------------
    # naming-convention would compute getTemperatureSp; the underlying hw
    # method is really named getTemperatureSP (see the original
    # Attribute2FunctionBase override - "SP" doesn't title-case correctly).
    def _temperature_sp_fget(self):
        return self._AndorInterface.getTemperatureSP()

    def _temperature_sp_fset(self, value):
        self._AndorInterface.setTemperatureSP(value)

    temperature_sp_attr = attribute(
        name="temperature_sp",
        dtype=int,
        access=AttrWriteType.READ_WRITE,
        unit="C",
        format="%1d",
        doc="in Celsius",
        fget=_temperature_sp_fget,
        fset=_temperature_sp_fset,
    )

    _temperature_fget, _ = AttrHelper.make_fget_fset(
        "temperature", lambda self: self._AndorInterface
    )
    temperature = attribute(
        dtype=int,
        access=AttrWriteType.READ,
        unit="C",
        format="%1d",
        doc="in Celsius",
        fget=_temperature_fget,
    )

    _cooler_fget, _cooler_fset = AttrHelper.make_fget_fset(
        "cooler", lambda self: self._AndorInterface, enum=_Cooler
    )
    cooler_attr = attribute(
        name="cooler",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="Start/stop the cooling system: ON or OFF",
        fget=_cooler_fget,
        fset=_cooler_fset,
    )

    _cooling_status_fget, _ = AttrHelper.make_fget_fset(
        "cooling_status", lambda self: self._AndorInterface
    )
    cooling_status = attribute(
        dtype=str,
        access=AttrWriteType.READ,
        label="Cooling status",
        doc="Tells if the setpoint temperature is reached",
        fget=_cooling_status_fget,
    )

    _fast_ext_trigger_fget, _fast_ext_trigger_fset = AttrHelper.make_fget_fset(
        "fast_ext_trigger", lambda self: self._AndorInterface, enum=_FastExtTrigger
    )
    fast_ext_trigger_attr = attribute(
        name="fast_ext_trigger",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="Fast trigger mode: OFF (default) or ON (don't wait for the keep-clean cycle)",
        fget=_fast_ext_trigger_fget,
        fset=_fast_ext_trigger_fset,
    )

    _shutter_level_fget, _shutter_level_fset = AttrHelper.make_fget_fset(
        "shutter_level", lambda self: self._AndorInterface, enum=_ShutterLevel
    )
    shutter_level_attr = attribute(
        name="shutter_level",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="Shutter output level: LOW or HIGH TTL signal to open the shutter",
        fget=_shutter_level_fget,
        fset=_shutter_level_fset,
    )


#----------------------------------------------------------------------------
# Plugins
#----------------------------------------------------------------------------

def get_control(config_path='/usr/local/etc/andor', serial_number=0,
                 _Andor=Andor, _Camera=AndorAcq.Camera, _Interface=AndorAcq.Interface,
                 **keys):
    camera = _Andor._AndorCamera
    interface = _Andor._AndorInterface

    if camera is None:
        print('\n\nStarting and configuring the Andor camera ...')
        camera = _Camera(config_path, int(serial_number))
        interface = _Interface(camera)
        print('\n\nAndor Camera %s: %s is started' % (camera.getDetectorType(), camera.getDetectorModel()))

    _Andor._AndorCamera = camera
    _Andor._AndorInterface = interface

    return core.CtControl(interface)

def get_tango_specific_class_n_device():
    return Andor.TangoClassClass, Andor
