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

import json
import sys
import os
import re
import urllib.request

# To change the format, modify the lines below:

# Markdown format:
output_file = "modlist.md"
format_url = "- [{Name}]({url}), v{Version} by **{Author}**: {Description}"
format_nourl = "- {Name}, v{Version} by **{Author}**: {Description}"

####################################

# Scan the manifest.json files of the mods in the pack
mods = []
def scan(basedir):
  res = False
  for file in os.listdir(basedir):
    if file[0] == ".": continue
    path = os.path.join(basedir, file, "manifest.json")
    if os.path.exists(path):
      try:
        with open(path, encoding="utf-8-sig") as f:
          data = f.read()
          # data = data.replace("\t", " ")
          data = re.sub("//.*?[\n]", "", data)
          data = re.sub(",\\s*([]}])", "\\1", data)
          info = json.loads(data)
        
        # Some data sanitization
        if "MajorVersion" in info["Version"]:
          version = info["Version"]
          version = [
            version["MajorVersion"],
            version["MinorVersion"],
            version["PatchVersion"],
            version["Build"],
          ]
          info["Version"] = ".".join([str(i) for i in version if not i is ""])
        
        # Add to our modlist.
        mods.append(info)
        res = True
      except err:
        print("Error: Failed to parse " + path, file=sys.stderr)
        print(err, file=sys.stderr)
    else:
      res2 = scan(os.path.join(basedir, file))
      if res2:
        res = True
      else:
        print("Warning: No mods found in " + path, file=sys.stderr)
  
  return res

print("Parsing manifest.json files", file=sys.stderr)
scan("Mods")
print("Sorting {0} mods".format(len(mods)), file=sys.stderr)
mods.sort(key=lambda x: x["Name"])

# Obtain mod info from smapi.io
fake_unique_id = 0
def mod_id(info):
  res = {}
  if "UniqueID" in info:
    res["id"] = info["UniqueID"]
  else:
    print("ERROR: UniqueID is missing for " + info["Name"], file=sys.stderr)
    res["id"] = info["UniqueID"] = "FAKE." + fake_unique_id
    fake_unique_id += 1
  if "UpdateKeys" in info:
    keys = [x for x in info["UpdateKeys"] if ":" in x]
    if keys:
      res["updateKeys"] = keys
  #res["installedVersion"] = info["Version"]
  return res

post_data = bytes(json.dumps({
  "mods": [mod_id(x) for x in mods],
  "includeExtendedMetadata": True
}),"utf-8")

#print(post_data)
print("Requesting better info from api.smapi.io", file=sys.stderr)
req = urllib.request.Request("https://api.smapi.io/v3.0/mods", method="POST", data=post_data)
req.add_header("Content-Type", "application/json")
res = urllib.request.urlopen(req)
if res.status != 200:
  print("Failed to obtain info from api.smapi.io: " + res.status + " " + res.reason, file=sys.stderr)
  os.exit(1)
print("Parsing response", file=sys.stderr)
better_info = {x["id"]:x["metadata"] for x in json.loads(str(res.read(), "utf-8")) if "main" in x["metadata"]}

# Output a formatted list of the mods contained in the pack.
def default(info, key, value):
  if not key in info:
    info[key] = value

def check_version(better, kind, version):
    return kind in better and version == better[kind]["version"]

stat_better = 0
stat_guessed = 0
def guess_url(info):
  global stat_better, stat_guessed
  if info["UniqueID"] in better_info:
    # SMAPI had info about this mod, obtain the url from there
    stat_better += 1
    better = better_info[info["UniqueID"]]
    version = info["Version"]
    if check_version(better, "optional", version):
      return better["optional"]["url"]
    if check_version(better, "unofficial", version):
      return better["unofficial"]["url"]
    return better["main"]["url"]

  # Otherwise, hope that the UpdateKeys have decent information.
  try:
    # It'll take the first updatekey
    key = info["UpdateKeys"][0]
  except:
    print("Update key is missing for " + info["Name"], file=sys.stderr)
    return None

  try:
    site, index = key.split(":")
  except:
    print("Update key is invalid for " + info["Name"] + ": '"+key+"'.", file=sys.stderr)
    return None

  if site == "Nexus":
    stat_guessed += 1
    return "https://www.nexusmods.com/stardewvalley/mods/" + index
  else:
    print("Unrecognized updatekey for " + info["Name"] + ": '"+key+"'.", file=sys.stderr)
    return None  

def report(info, f_out):
  default(info, "Author", "(unknown)")
  default(info, "Description", "-")

  url = guess_url(info)
  
  if url:
    print(format_url.format(url = url, **info), file=f_out)
  else:
    print(format_nourl.format(**info), file=f_out)

print("Writing output", file=sys.stderr)
with open(output_file, 'w') as f_out:
  for i in mods:
    report(i, f_out)

print("Done ({0} mods, with {1} guessed and {2} better urls).".format(len(mods), stat_guessed, stat_better), file=sys.stderr)

