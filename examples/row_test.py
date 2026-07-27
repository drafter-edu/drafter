from drafter import *

from bakery import assert_equal



assert_equal(Row("First", "Second"), Row("First", "Second"))

assert_equal(Row("A", "B", "C", style_font_color="red"),
             Row("A", "B", "C", style_font_color= 'red',
                 style_display='flex', style_flex_direction='row',
                 style_align_items='center'))

assert_equal(Row("A", "B", "C", style_font_color="red"),
             Row("A", "B", "C", extra_settings=dict(style_font_color= 'red',
                 style_display='flex', style_flex_direction='row',
                 style_align_items='center')))

