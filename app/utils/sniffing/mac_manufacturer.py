# -*- coding: utf-8 -*-

"""
*********************************************************************************
*                                                                               *
* pcap.py -- Packet Capture (pcap)                                              *
*                                                                               *
* Methods to sniff the network traffic through pyshark.                         *
*                                                                               *
* pyshark repository:                                                           *
* https://github.com/KimiNewt/pyshark                                           *
*                                                                               *
* pyshark license:                                                              *
* https://raw.githubusercontent.com/KimiNewt/pyshark/master/LICENSE.txt         *
*                                                                               *
********************** IMPORTANT BLACK-WIDOW LICENSE TERMS **********************
*                                                                               *
* This file is part of black-widow.                                             *
*                                                                               *
* black-widow is free software: you can redistribute it and/or modify           *
* it under the terms of the GNU General Public License as published by          *
* the Free Software Foundation, either version 3 of the License, or             *
* (at your option) any later version.                                           *
*                                                                               *
* black-widow is distributed in the hope that it will be useful,                *
* but WITHOUT ANY WARRANTY; without even the implied warranty of                *
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                 *
* GNU General Public License for more details.                                  *
*                                                                               *
* You should have received a copy of the GNU General Public License             *
* along with black-widow.  If not, see <http://www.gnu.org/licenses/>.          *
*                                                                               *
*********************************************************************************
"""

from math import floor

from app.utils.helpers.logger import Log
from app.utils.requests import request


class MacManufacturer:
    """
    The Mac Manufacturer Lookup class
    _________________________
    | 1 | 2 | 3 | 4 | 5 | 6 |  =  48bit (6 * 8bit)
    {^^^^OUI^^^}^{^^^NIC^^^^}

    MAC Address: 6 Octets -> First 3 Octets:  OUI "Organisationally Unique Identifier"
                                   |--- 1st Octet: 7th bit (1=locally administered, 0=globally unique)
                                                   8th bit (0=unicast, 1=multicast)
                             Second 3 Octets: NIC "Network Interface Controller"
    """

    MANUFACTURERS_URL = 'https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf'
    MANUFACTURERS_DETAIL_DICT = {
        0: 'mac',
        1: 'vendor',
        2: 'company',
        3: 'comment'
    }

    def __init__(self):
        self.manufacturer_dict = dict()
        self._update_manufacturer_dict()

    def lookup(self, mac: str) -> dict or None:
        """
        Lookup the mac address
        :param mac: The mac address to lookup
        :rtype: dict or None
        """
        for i in range(len(mac), 0, -1):
            manufacturer = self.manufacturer_dict.get(mac[0:i])
            if manufacturer is not None:
                return manufacturer
        return None

    def _update_manufacturer_dict(self):
        manufacturer_response = request(MacManufacturer.MANUFACTURERS_URL)
        if manufacturer_response.text is None:
            return
        self.manufacturer_dict = dict()
        manufacturer_list = manufacturer_response.text.splitlines()
        for manufacturer in manufacturer_list:
            if len(manufacturer) < 1:
                continue
            if manufacturer[0] == '#':
                continue
            manufacturer_details = manufacturer.split('\t')
            i = 0
            mac = None
            lookup_dict = {
                MacManufacturer.MANUFACTURERS_DETAIL_DICT[1]: None,
                MacManufacturer.MANUFACTURERS_DETAIL_DICT[2]: None,
                MacManufacturer.MANUFACTURERS_DETAIL_DICT[3]: None
            }
            for detail in manufacturer_details:
                if detail == '':
                    continue
                if i == 0:
                    # MAC address
                    mac_detail = detail.split('/')
                    if len(mac_detail) == 2:
                        # The mac has a sub mask, so the dict key is the first n bits
                        sub_mask = int(mac_detail[1]) / 4
                        mac_sub_mask = floor(sub_mask + (sub_mask / 2))
                        mac = mac_detail[0][0:mac_sub_mask]
                    elif len(mac_detail) == 1:
                        # The mac has not a sub mask
                        mac = mac_detail[0]
                    else:
                        Log.error("Wrong mac address: " + str(detail))
                        break
                if i >= len(MacManufacturer.MANUFACTURERS_DETAIL_DICT):
                    Log.error("Wrong manufacturer details: " + str(manufacturer_details))
                    break
                lookup_dict[MacManufacturer.MANUFACTURERS_DETAIL_DICT[i]] = detail
                i += 1
            if mac is None:
                Log.error("Wrong manufacturer details: " + str(manufacturer_details))
                continue
            self.manufacturer_dict[mac] = lookup_dict
