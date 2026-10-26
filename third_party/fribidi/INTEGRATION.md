# FriBidi integration

This directory vendors GNU FriBidi 1.0.13 from the upstream tag `v1.0.13` at commit `b54871c339dabb7434718da3fed2fa63320997e5` (`https://github.com/fribidi/fribidi`). The upstream library is licensed under LGPL-2.1-or-later; see `COPYING`. The app builds the library sources directly into its PS4 executable, with generated Unicode tables committed under `lib/` so ordinary builds do not require Meson or a system FriBidi library.

`config.h` is the project’s OpenOrbis target configuration; `lib/fribidi-config.h` and the Unicode tables are generated from upstream FriBidi 1.0.13. `tools/build_ps4.py` records hashes of all compiled inputs. The application includes the complete library source and this notice so maintainers can rebuild and replace the LGPL component.

The Arabic UI uses FriBidi for Unicode bidirectional ordering and Arabic presentation-form shaping. It does not provide full OpenType GPOS positioning for optional combining marks; current UI copy intentionally avoids vocalization marks.
