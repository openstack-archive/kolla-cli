# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from blaze.api.properties import PropertyApi as BlazePropertyApi
from kollacli.common.utils import reraise

GLOBAL_TYPE = 'global'


class PropertyApi(object):

    class Property(object):
        """Property

        Members:
            - name (str): key
            - value (str): value
            - file_name (str): name of file property is from
            - overrides (bool): does the property override some other value
            - orig_value (str): the value which is overridden or None
            - target (str): group or host name for group or host properties
            - prop_type (str): one of 'global', 'group' or 'host'
            - ovr_global (bool): true if property is overridden at global level
            - ovr_group (bool): true if property is overridden at group level
            - ovr_host (bool): true if property is overridden at host level
        """
        def __init__(self):
            self.name = None
            self.value = None
            self.file_name = None
            self.overrides = None
            self.orig_value = None
            self.target = None
            self.prop_type = None

            self.ovr_global = None
            self.ovr_group = None
            self.ovr_host = None

    def property_set(self, property_dict,
                     property_type=GLOBAL_TYPE, change_set=None):
        """Set a property

        :param property_dict: property dictionary containing key / values
        :type property_dict: dictionary
        :param property_type: one of 'global', 'group' or 'host'
        :type property_type: string
        :param change_set: for group or host sets this is the list of groups
                           or hosts to set the property for
        :type change_set: list of strings

        """
        try:
            BlazePropertyApi().property_set(property_dict,
                                            property_type, change_set)
        except Exception as e:
            reraise(e)

    def property_clear(self, property_list, property_type=GLOBAL_TYPE,
                       change_set=None):
        """Clear a property

        :param property_list: property list
        :type property_list: list
        :param property_type: one of 'global', 'group' or 'host'
        :type property_type: string
        :param change_set: for group or host clears this is the list of
                           groups or hosts to clear the property for
        :type change_set: list of strings

        """
        try:
            BlazePropertyApi().property_clear(property_list,
                                              property_type, change_set)
        except Exception as e:
            reraise(e)

    def property_get(self, property_type=GLOBAL_TYPE, get_set=None):
        """Returns a list of Property objects

        :param property_type: one of 'global', 'group', or 'host'
        :type property_type: string
        :param get_set: optional list of hosts or groups to be used when
                         getting group or host related property lists
        :type get_set: list of strings
        :return: properties
        :rtype: list of Property objects
        """
        try:
            properties = BlazePropertyApi().property_get(property_type,
                                                         get_set)
            new_properties = []
            for prop in properties:
                new_prop = self.Property()
                new_prop.name = prop.name
                new_prop.value = prop.value
                new_prop.file_name = prop.file_name
                new_prop.overrides = prop.overrides
                new_prop.orig_value = prop.orig_value
                new_prop.target = prop.target
                new_prop.prop_type = prop.prop_type
                new_prop.ovr_global = prop.ovr_global
                new_prop.ovr_group = prop.ovr_group
                new_prop.ovr_host = prop.ovr_host
                new_properties.append(new_prop)
            return new_properties
        except Exception as e:
            reraise(e)
