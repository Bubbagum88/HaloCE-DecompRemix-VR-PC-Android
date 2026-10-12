# Test64 checklist (VR SETTINGS crash)

Source: the owner's Test63 session (`halo_log_2026-10-12_14-09-57`) and
message: "crashed the game when opening vr settings". Columns:
**Implemented**, **Automated** (host check), **Device** (Quest/phone only).

## Evidence

| Observation | Cause found | Test64 |
|---|---|---|
| 14:10:38.685 pointer click, then `signal 11 at address 0x70696e73` (the text "snip" read as a pointer); the shipped VR guest (sha256 `8fa9ff31...50a0`) maps the stack to `strnlen` < `vsnprintf` < `vr_menu_setting_text` < `widget_instance_render_recursive` | `vr_menu_paged` built Test63's settings index for the list of categories too (`group = VR_MENU_PAGE_COUNT`, 17 categories = three screens) and named each row from `vr_menu_pages[VR_MENU_PAGE_COUNT].settings[...]`, one past the table | The index is built only for a category's own pages (`group < VR_MENU_PAGE_COUNT`); the category list keeps its NEXT paging |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| VR SETTINGS opens | `vr_menu.c` `vr_menu_paged` | test_test31_vr_menu now has 17 categories as the game does: without the fix AddressSanitizer reports global-buffer-overflow in `vr_menu_paged`; with it the suite passes | Open VR SETTINGS |
| Category sections index unchanged | same | test_test31_vr_menu (three-topic page opens its index) | Open IMMERSION |
| Everything else in Test63 | unchanged | full suite | `TEST63-DEVICE-CHECKLIST.md` |
