#!/usr/bin/python3 
#
# A script to collect modpack info for Stardew Valley.
# Copyright (C) 2019  Bauke Conijn <bcmpinc@users.sourceforge.net>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import yaml
import sys
import os
import re

# To change the format, modify the lines below:
format_url = "- [{Name}]({url}), v{Version} by **{Author}**: {Description}"
format_nourl = "- {Name}, v{Version} by **{Author}**: {Description}"

def default(info, key, value):
    if not key in info:
        info[key] = value

def report(info):
    default(info, "Author", "(unknown)")
    default(info, "Description", "-")
    if "MajorVersion" in info["Version"]:
        version = info["Version"]
        version = [
            version["MajorVersion"],
            version["MinorVersion"],
            version["PatchVersion"],
            version["Build"],
        ]
        info["Version"] = ".".join([str(i) for i in version if not i is ""])

    try:
        # It'll take the first updatekey
        key = info["UpdateKeys"][0]
    except:
        print("Update key is missing.", file=sys.stderr)
        print(format_nourl.format(**info))
        return

    try:
        site, index = key.split(":")
    except:
        print("Update key is invalid: '"+key+"'.", file=sys.stderr)
        print(format_nourl.format(**info))
        return

    if site == "Nexus":
        url = "https://www.nexusmods.com/stardewvalley/mods/" + index
    else:
        print("Unrecognized updatekey: '"+key+"'.", file=sys.stderr)
        print(format_nourl.format(**info))
        return
    
    print("OK.", file=sys.stderr)
    print(format_url.format(url = url, **info))


def scan(basedir):
    for file in os.listdir(basedir):
        print(file, file=sys.stderr, end=" : ")
        path = os.path.join(basedir, file, "manifest.json")
        if os.path.exists(path):
            with open(path) as f:
                data = f.read()
                data = data.replace("\t", " ")
                data = re.sub("//.*?[\n]", "", data)
                json = yaml.load(data, Loader=yaml.FullLoader)
            report(json)
        else:
            scan(os.path.join(basedir, file))

scan("Mods")
