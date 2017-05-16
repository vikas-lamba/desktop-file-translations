#
# Copyright (c) 2017 SUSE Linux GmbH
#
# This file is part of tar2po.
#
# tar2po is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# tar2po is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with tar2po. If not, see <http://www.gnu.org/licenses/>.

"""
This file parses XML files uses for appstream metadata,
polkit actions and mineinfo and generates PO and POT files.
"""

import os
import re


TRANSLATABLE_ENTRIES = {"Desktop Entry":
                        ["GenericName", "Name", "Comment", "Keywords", "X-KDE-Keywords"]
                        }

# This is a special case, the section name can vary
DESKTOPACTION_RE = re.compile("Desktop Action [^\]]+")

COMMENT_RE = re.compile("#.*")
SECTION_RE = re.compile("\[([^\]]+)\]")
ENTRY_RE = re.compile("([^\[=]+)(\[([^=\]]+)\])?\s*=\s*(.*)")


def extractDesktopLangInfo(file, filepath, type):
    """
    Parses file as desktop file (of the specified type, see getFileType).
    @returns dict:
    {"Comment(org.opensuse.asdf)":
        {'file': "/usr/share/applications/org.opensuse.asdf.desktop", 'line': 42,
         'key': "Comment", 'section': "Desktop File",
         'values': {"": "Example", "de": "Beispiel", ...
        },
        ...
    }
    """

    translations = {}
    lineno = 0
    current_section = None
    # Identifier of the desktop file
    basename = os.path.basename(filepath)

    # Step 1: Read all entries + translations into translations
    for line in file:
        lineno += 1
        line = line.decode("utf-8")

        if len(line.strip()) == 0 or COMMENT_RE.match(line):
            continue

        section_match = SECTION_RE.match(line)

        if section_match:
            current_section = section_match.group(1)
            continue

        entry_match = ENTRY_RE.match(line)
        if not entry_match:
            print("Warning: Could not parse desktop file line '{}'!".format(line[:-1]))

        (key, lang, value) = entry_match.group(1, 3, 4)

        assert key is not None

        if current_section == "Desktop Entry":
            ctxt = "{}({})".format(key, basename)
        else:
            ctxt = "{}-{}({})".format(current_section, key, basename)

        if ctxt not in translations:
            translations[ctxt] = {'file': filepath, 'line': lineno,
                                  'section': current_section, 'key': key,
                                  'values': {}}

        if lang is None:
            translations[ctxt]['line'] = lineno
            lang = ''

        if lang in translations[ctxt]['values']:
            print("Warning: Found entry {}{} more than once in {}:{}!".format(key, "" if lang == '' else "(lang {})".format(lang), filepath, line[:-1]))

        translations[ctxt]['values'][lang] = value

    # Step 2: Various warnings + clean up
    for ctxt in list(translations.keys()):
        translation = translations[ctxt]
        # Step 2.1: Warn for invalid translations (no vanilla string)
        if "" not in translation['values']:
            print("Warning: Invalid translation {} at {}:{}".format(ctxt, translation['file'], translation['line']))
            translations.pop(ctxt)
        elif translation['section'] in TRANSLATABLE_ENTRIES and translation['key'] in TRANSLATABLE_ENTRIES[translation['section']]:
            pass  # Keep
        elif DESKTOPACTION_RE.match(translation['section']):
            pass  # Keep
        # Step 2.2: Warn if translated but not in TRANSLATABLE_ENTRIES
        elif len(translation['values']) > 1:
            print("Warning: Unexpected translation for {} at {}:{}".format(ctxt, translation['file'], translation['line']))
            # Keep to not lose upstream translations
        # Step 2.3:
        else:
            # Not translatable and no translations
            translations.pop(ctxt)

    return translations
