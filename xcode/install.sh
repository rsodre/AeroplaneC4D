#!/bin/sh

# Delete C4D attributes cache
# Find your folder in Edit > Preferences > Open Preferences folder
export PREFERENCES_FOLDER="$HOME/Library/Preferences/MAXON/CINEMA 4D R19_8DA1506D"
rm -f "$PREFERENCES_FOLDER/prefs/symbolcache"

# Copy plugin to C4D
export PLUGINS_FOLDER="/Applications/MAXON/CINEMA 4D R19/plugins"
rm -rf "$PLUGINS_FOLDER/Aeroplane"
cp -R ../Aeroplane "$PLUGINS_FOLDER"
