# Synthetic ADV2 decoder fixture

adv2_fixture.adv contains three generated 8x4 uint16 detector images, not observations.
Regenerate with build_tools/make_adv_fixture.py and the pinned ADVCore native library.
Pixels are 1000 + frame index + row-major pixel index. Exposure is 200000000 ns;
midpoint UTC since 2010-01-01 is 1100000123 + frame index * 300000000 ns.
The fixture is decoded through the application's worker in unit and frozen tests.
