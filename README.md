# GoldSrc Server List

This project keeps a sorted list of public game servers made with GoldSrc.

It is generated automatically from the Steam master server data, filtered to valid GoldSrc-compatible servers, and grouped by game directory such as `cstrike`, `valve` and etc. The result is published as static files so it can be consumed by Xash3D-FWGS.

## What this project does

- Queries Steam for public server candidates
- Verifies each server by sending a GoldSrc Source Engine query
- Filters out invalid or non-GoldSrc entries
- Sorts and groups servers by game directory
- Saves each group in a plain text list like:

```
gs 1.2.3.4:27015
gs 5.6.7.8:27015
```

## Why it exists

This list is meant to make GoldSrc server discovery easier in Xash3D-FWGS. Instead of manually adding many server addresses, you can point Xash3D-FWGS to the generated master list and have those servers appear in the game browser.

## Use with Xash3D-FWGS

Run this command in Xash3D-FWGS:

```
addmasterstatic https://elinsrc.github.io/goldsrc-list
```

This adds the generated GoldSrc master server list and makes the servers in this repository visible in Xash3D-FWGS.