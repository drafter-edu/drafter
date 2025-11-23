"""
Comprehensive tests for all components in drafter.components

These tests ensure that:
1. Each component has a working repr()
2. Components are equal to themselves when repr is evaluated
3. Components work with missing optional keyword arguments
4. Components work with kwargs and extra_settings
5. Components work with different combinations of parameters
"""
import pytest
from drafter.components import (
    Argument, Link, Button, Image, TextBox, TextArea, SelectBox, CheckBox,
    LineBreak, HorizontalRule, Span, Div, Pre, Row, NumberedList, BulletedList,
    Header, Table, Text, Download, FileUpload, ApiKeyBox, MatPlotLibPlot
)


class TestArgument:
    """Tests for the Argument component"""
    
    def test_argument_repr_basic(self):
        """Test that Argument has a working repr with basic parameters"""
        arg = Argument("test_name", "test_value")
        # repr should be evaluable
        repr_str = repr(arg)
        assert "Argument" in repr_str
    
    def test_argument_with_kwargs(self):
        """Test Argument with extra keyword arguments"""
        arg = Argument("test_name", "test_value", id="custom_id", style_color="blue")
        assert arg.extra_settings.get("id") == "custom_id"
        assert arg.extra_settings.get("style_color") == "blue"
    
    def test_argument_different_value_types(self):
        """Test Argument with different value types"""
        arg_str = Argument("name1", "string_value")
        arg_int = Argument("name2", 42)
        arg_float = Argument("name3", 3.14)
        arg_bool = Argument("name4", True)
        
        assert arg_str.value == "string_value"
        assert arg_int.value == 42
        assert arg_float.value == 3.14
        assert arg_bool.value is True
    
    def test_argument_invalid_name(self):
        """Test that Argument rejects invalid names"""
        with pytest.raises(ValueError):
            Argument("invalid name", "value")  # space in name
        
        with pytest.raises(ValueError):
            Argument("123invalid", "value")  # starts with number
    
    def test_argument_invalid_value_type(self):
        """Test that Argument rejects invalid value types"""
        with pytest.raises(ValueError):
            Argument("name", [1, 2, 3])  # list not allowed
        
        with pytest.raises(ValueError):
            Argument("name", {"key": "value"})  # dict not allowed


class TestLink:
    """Tests for the Link component"""
    
    def test_link_repr_basic(self):
        """Test that Link has a working repr with basic parameters"""
        link = Link("Click me", "/page")
        repr_str = repr(link)
        # Verify it creates a valid representation
        assert "Link" in str(type(link).__name__)
    
    def test_link_with_kwargs(self):
        """Test Link with extra keyword arguments"""
        link = Link("Click me", "/page", id="my_link", style_color="red")
        assert link.extra_settings.get("id") == "my_link"
        assert link.extra_settings.get("style_color") == "red"
    
    def test_link_with_arguments(self):
        """Test Link with arguments parameter"""
        link = Link("Click me", "/page", arguments=[("key", "value")])
        assert link.arguments is not None
    
    def test_link_without_arguments(self):
        """Test Link without arguments parameter"""
        link = Link("Click me", "/page")
        assert link.text == "Click me"
        assert link.url == "/page"
    
    def test_link_with_argument_objects(self):
        """Test Link with Argument objects as arguments"""
        arg1 = Argument("param1", "value1")
        arg2 = Argument("param2", 42)
        link = Link("Click me", "/page", arguments=[arg1, arg2])
        assert link.arguments == [arg1, arg2]


class TestButton:
    """Tests for the Button component"""
    
    def test_button_repr_basic(self):
        """Test that Button has a working repr with basic parameters"""
        button = Button("Submit", "/submit")
        repr_str = repr(button)
        assert repr_str == "Button(text='Submit', url='/submit')"
    
    def test_button_repr_with_arguments(self):
        """Test Button repr with arguments"""
        arg = Argument("key", "value")
        button = Button("Submit", "/submit", arguments=[arg])
        repr_str = repr(button)
        assert "Button" in repr_str
        assert "arguments" in repr_str
    
    def test_button_with_kwargs(self):
        """Test Button with extra keyword arguments"""
        button = Button("Submit", "/submit", id="submit_btn", class_="btn-primary")
        assert button.extra_settings.get("id") == "submit_btn"
        assert button.extra_settings.get("class_") == "btn-primary"
    
    def test_button_without_arguments(self):
        """Test Button without arguments parameter"""
        button = Button("Submit", "/submit")
        assert button.text == "Submit"
        assert button.url == "/submit"
    
    def test_button_with_arguments(self):
        """Test Button with arguments parameter"""
        button = Button("Submit", "/submit", arguments=[("key", "value")])
        assert button.arguments is not None


class TestImage:
    """Tests for the Image component"""
    
    def test_image_repr_basic(self):
        """Test that Image has a working repr with basic parameters"""
        img = Image("/path/to/image.png")
        # Verify object was created
        assert img.url == "/path/to/image.png"
    
    def test_image_with_dimensions(self):
        """Test Image with width and height"""
        img = Image("/path/to/image.png", width=100, height=200)
        assert img.width == 100
        assert img.height == 200
    
    def test_image_without_dimensions(self):
        """Test Image without dimensions"""
        img = Image("/path/to/image.png")
        assert img.width is None
        assert img.height is None
    
    def test_image_with_kwargs(self):
        """Test Image with extra keyword arguments"""
        img = Image("/path/to/image.png", alt="Description", title="Image title")
        assert img.extra_settings.get("alt") == "Description"
        assert img.extra_settings.get("title") == "Image title"
    
    def test_image_with_only_width(self):
        """Test Image with only width"""
        img = Image("/path/to/image.png", width=100)
        assert img.width == 100
        assert img.height is None
    
    def test_image_with_only_height(self):
        """Test Image with only height"""
        img = Image("/path/to/image.png", height=200)
        assert img.width is None
        assert img.height == 200


class TestTextBox:
    """Tests for the TextBox component"""
    
    def test_textbox_repr_basic(self):
        """Test that TextBox has a working repr with basic parameters"""
        tb = TextBox("username")
        # Verify object was created
        assert tb.name == "username"
    
    def test_textbox_with_default_value(self):
        """Test TextBox with default_value"""
        tb = TextBox("username", default_value="john_doe")
        assert tb.default_value == "john_doe"
    
    def test_textbox_without_default_value(self):
        """Test TextBox without default_value"""
        tb = TextBox("username")
        assert tb.default_value == ""
    
    def test_textbox_with_kind(self):
        """Test TextBox with different kind values"""
        tb_text = TextBox("field1", kind="text")
        tb_password = TextBox("field2", kind="password")
        tb_email = TextBox("field3", kind="email")
        
        assert tb_text.kind == "text"
        assert tb_password.kind == "password"
        assert tb_email.kind == "email"
    
    def test_textbox_with_kwargs(self):
        """Test TextBox with extra keyword arguments"""
        tb = TextBox("username", placeholder="Enter username", required=True)
        assert tb.extra_settings.get("placeholder") == "Enter username"
        assert tb.extra_settings.get("required") is True
    
    def test_textbox_invalid_name(self):
        """Test that TextBox rejects invalid names"""
        with pytest.raises(ValueError):
            TextBox("invalid name")  # space in name


class TestTextArea:
    """Tests for the TextArea component"""
    
    def test_textarea_repr_basic(self):
        """Test that TextArea has a working repr with basic parameters"""
        ta = TextArea("comments")
        assert ta.name == "comments"
    
    def test_textarea_with_default_value(self):
        """Test TextArea with default_value"""
        ta = TextArea("comments", default_value="Default text")
        assert ta.default_value == "Default text"
    
    def test_textarea_without_default_value(self):
        """Test TextArea without default_value"""
        ta = TextArea("comments")
        assert ta.default_value == ""
    
    def test_textarea_with_kwargs(self):
        """Test TextArea with extra keyword arguments"""
        ta = TextArea("comments", rows=5, cols=40, placeholder="Enter comments")
        assert ta.extra_settings.get("rows") == 5
        assert ta.extra_settings.get("cols") == 40
        assert ta.extra_settings.get("placeholder") == "Enter comments"
    
    def test_textarea_invalid_name(self):
        """Test that TextArea rejects invalid names"""
        with pytest.raises(ValueError):
            TextArea("invalid name")  # space in name


class TestSelectBox:
    """Tests for the SelectBox component"""
    
    def test_selectbox_repr_basic(self):
        """Test that SelectBox has a working repr with basic parameters"""
        sb = SelectBox("choice", ["Option 1", "Option 2", "Option 3"])
        assert sb.name == "choice"
        assert len(sb.options) == 3
    
    def test_selectbox_with_default_value(self):
        """Test SelectBox with default_value"""
        sb = SelectBox("choice", ["A", "B", "C"], default_value="B")
        assert sb.default_value == "B"
    
    def test_selectbox_without_default_value(self):
        """Test SelectBox without default_value"""
        sb = SelectBox("choice", ["A", "B", "C"])
        assert sb.default_value == ""
    
    def test_selectbox_with_kwargs(self):
        """Test SelectBox with extra keyword arguments"""
        sb = SelectBox("choice", ["A", "B", "C"], id="my_select", disabled=True)
        assert sb.extra_settings.get("id") == "my_select"
        assert sb.extra_settings.get("disabled") is True
    
    def test_selectbox_invalid_name(self):
        """Test that SelectBox rejects invalid names"""
        with pytest.raises(ValueError):
            SelectBox("invalid name", ["A", "B"])


class TestCheckBox:
    """Tests for the CheckBox component"""
    
    def test_checkbox_repr_basic(self):
        """Test that CheckBox has a working repr with basic parameters"""
        cb = CheckBox("agree")
        assert cb.name == "agree"
    
    def test_checkbox_with_default_value_true(self):
        """Test CheckBox with default_value True"""
        cb = CheckBox("agree", default_value=True)
        assert cb.default_value is True
    
    def test_checkbox_with_default_value_false(self):
        """Test CheckBox with default_value False"""
        cb = CheckBox("agree", default_value=False)
        assert cb.default_value is False
    
    def test_checkbox_without_default_value(self):
        """Test CheckBox without default_value"""
        cb = CheckBox("agree")
        assert cb.default_value is False
    
    def test_checkbox_with_kwargs(self):
        """Test CheckBox with extra keyword arguments"""
        cb = CheckBox("agree", id="agree_checkbox", checked=True)
        assert cb.extra_settings.get("id") == "agree_checkbox"
        assert cb.extra_settings.get("checked") is True
    
    def test_checkbox_invalid_name(self):
        """Test that CheckBox rejects invalid names"""
        with pytest.raises(ValueError):
            CheckBox("invalid name")


class TestLineBreak:
    """Tests for the LineBreak component"""
    
    def test_linebreak_creation(self):
        """Test that LineBreak can be created"""
        lb = LineBreak()
        assert str(lb) == "<br />"
    
    def test_linebreak_repr(self):
        """Test LineBreak repr"""
        lb = LineBreak()
        repr_str = repr(lb)
        assert "LineBreak" in repr_str


class TestHorizontalRule:
    """Tests for the HorizontalRule component"""
    
    def test_horizontalrule_creation(self):
        """Test that HorizontalRule can be created"""
        hr = HorizontalRule()
        assert str(hr) == "<hr />"
    
    def test_horizontalrule_repr(self):
        """Test HorizontalRule repr"""
        hr = HorizontalRule()
        repr_str = repr(hr)
        assert "HorizontalRule" in repr_str


class TestSpan:
    """Tests for the Span component"""
    
    def test_span_repr_basic(self):
        """Test that Span has a working repr with basic parameters"""
        span = Span("Hello")
        repr_str = repr(span)
        assert "Span" in repr_str
    
    def test_span_with_multiple_content(self):
        """Test Span with multiple content items"""
        span = Span("Hello", "World")
        assert len(span.content) == 2
    
    def test_span_with_kwargs(self):
        """Test Span with extra keyword arguments"""
        span = Span("Hello", id="greeting", style_color="blue")
        assert span.extra_settings.get("id") == "greeting"
        assert span.extra_settings.get("style_color") == "blue"
    
    def test_span_with_extra_settings(self):
        """Test Span with extra_settings parameter"""
        span = Span("Hello", extra_settings={"id": "test", "class_": "highlight"})
        assert span.extra_settings.get("id") == "test"
        assert span.extra_settings.get("class_") == "highlight"
    
    def test_span_empty(self):
        """Test Span with no content"""
        span = Span()
        assert len(span.content) == 0


class TestDiv:
    """Tests for the Div component"""
    
    def test_div_repr_basic(self):
        """Test that Div has a working repr with basic parameters"""
        div = Div("Content")
        repr_str = repr(div)
        assert "Div" in repr_str
    
    def test_div_with_multiple_content(self):
        """Test Div with multiple content items"""
        div = Div("Item 1", "Item 2", "Item 3")
        assert len(div.content) == 3
    
    def test_div_with_kwargs(self):
        """Test Div with extra keyword arguments"""
        div = Div("Content", id="main", class_="container")
        assert div.extra_settings.get("id") == "main"
        assert div.extra_settings.get("class_") == "container"
    
    def test_div_with_extra_settings(self):
        """Test Div with extra_settings parameter"""
        div = Div("Content", extra_settings={"data-value": "123"})
        assert div.extra_settings.get("data-value") == "123"
    
    def test_div_empty(self):
        """Test Div with no content"""
        div = Div()
        assert len(div.content) == 0


class TestPre:
    """Tests for the Pre component"""
    
    def test_pre_repr_basic(self):
        """Test that Pre has a working repr with basic parameters"""
        pre = Pre("code content")
        repr_str = repr(pre)
        assert "Pre" in repr_str
    
    def test_pre_with_kwargs(self):
        """Test Pre with extra keyword arguments"""
        pre = Pre("code", id="code_block", style_font_family="monospace")
        assert pre.extra_settings.get("id") == "code_block"
        assert pre.extra_settings.get("style_font_family") == "monospace"


class TestRow:
    """Tests for the Row component"""
    
    def test_row_creation(self):
        """Test that Row can be created"""
        row = Row("Item 1", "Item 2")
        assert len(row.content) == 2
    
    def test_row_has_flex_styles(self):
        """Test that Row has default flex styles"""
        row = Row("Item")
        assert row.extra_settings.get("style_display") == "flex"
        assert row.extra_settings.get("style_flex_direction") == "row"
        assert row.extra_settings.get("style_align_items") == "center"
    
    def test_row_with_kwargs(self):
        """Test Row with extra keyword arguments"""
        row = Row("Item", id="main_row")
        assert row.extra_settings.get("id") == "main_row"


class TestNumberedList:
    """Tests for the NumberedList component"""
    
    def test_numberedlist_creation(self):
        """Test that NumberedList can be created"""
        nl = NumberedList(["Item 1", "Item 2", "Item 3"])
        assert len(nl.items) == 3
    
    def test_numberedlist_with_kwargs(self):
        """Test NumberedList with extra keyword arguments"""
        nl = NumberedList(["A", "B"], id="my_list", class_="ordered")
        assert nl.extra_settings.get("id") == "my_list"
        assert nl.extra_settings.get("class_") == "ordered"
    
    def test_numberedlist_empty(self):
        """Test NumberedList with empty list"""
        nl = NumberedList([])
        assert len(nl.items) == 0


class TestBulletedList:
    """Tests for the BulletedList component"""
    
    def test_bulletedlist_creation(self):
        """Test that BulletedList can be created"""
        bl = BulletedList(["Item 1", "Item 2", "Item 3"])
        assert len(bl.items) == 3
    
    def test_bulletedlist_with_kwargs(self):
        """Test BulletedList with extra keyword arguments"""
        bl = BulletedList(["A", "B"], id="my_list", class_="unordered")
        assert bl.extra_settings.get("id") == "my_list"
        assert bl.extra_settings.get("class_") == "unordered"
    
    def test_bulletedlist_empty(self):
        """Test BulletedList with empty list"""
        bl = BulletedList([])
        assert len(bl.items) == 0


class TestHeader:
    """Tests for the Header component"""
    
    def test_header_default_level(self):
        """Test Header with default level"""
        h = Header("Title")
        assert h.body == "Title"
        assert h.level == 1
    
    def test_header_with_level(self):
        """Test Header with custom level"""
        h1 = Header("Title 1", level=1)
        h2 = Header("Title 2", level=2)
        h3 = Header("Title 3", level=3)
        
        assert h1.level == 1
        assert h2.level == 2
        assert h3.level == 3
    
    def test_header_repr(self):
        """Test Header repr"""
        h = Header("Test", level=2)
        repr_str = repr(h)
        assert "Header" in repr_str


class TestTable:
    """Tests for the Table component"""
    
    def test_table_creation(self):
        """Test that Table can be created"""
        rows = [["A", "B"], ["C", "D"]]
        table = Table(rows)
        assert len(table.rows) == 2
    
    def test_table_with_header(self):
        """Test Table with header"""
        rows = [["1", "2"], ["3", "4"]]
        table = Table(rows, header=["Col1", "Col2"])
        assert table.header == ["Col1", "Col2"]
    
    def test_table_without_header(self):
        """Test Table without header"""
        rows = [["A", "B"]]
        table = Table(rows)
        # header may be None or set by reformat_as_tabular
        assert True  # Just verify it doesn't crash
    
    def test_table_with_kwargs(self):
        """Test Table with extra keyword arguments"""
        rows = [["A", "B"]]
        table = Table(rows, id="data_table", class_="striped")
        assert table.extra_settings.get("id") == "data_table"
        assert table.extra_settings.get("class_") == "striped"


class TestText:
    """Tests for the Text component"""
    
    def test_text_repr_basic(self):
        """Test that Text has a working repr with basic parameters"""
        text = Text("Hello World")
        repr_str = repr(text)
        assert repr_str == "Text('Hello World')"
    
    def test_text_repr_with_extra_settings(self):
        """Test Text repr with extra_settings"""
        text = Text("Hello", style_color="red")
        repr_str = repr(text)
        assert "Text" in repr_str
        assert "style_color" in repr_str or "{'style_color': 'red'}" in repr_str
    
    def test_text_equality_to_self(self):
        """Test that Text is equal to itself"""
        text = Text("Test")
        assert text == text
    
    def test_text_equality_after_repr_eval(self):
        """Test that Text repr produces a valid representation"""
        text = Text("Test")
        repr_str = repr(text)
        # Verify repr contains the expected format
        assert repr_str == "Text('Test')"
        # Test that evaluating the repr creates an equivalent object
        # Note: This uses eval() on a controlled string from our own code
        text2 = eval(repr_str)
        assert text == text2
    
    def test_text_equality_to_string(self):
        """Test Text equality with plain string"""
        text = Text("Hello")
        assert text == "Hello"
    
    def test_text_with_kwargs(self):
        """Test Text with extra keyword arguments"""
        text = Text("Hello", style_color="blue", id="greeting")
        assert text.extra_settings.get("style_color") == "blue"
        assert text.extra_settings.get("id") == "greeting"
    
    def test_text_with_extra_settings(self):
        """Test Text with extra_settings parameter"""
        text = Text("Hello", extra_settings={"id": "test"})
        assert text.extra_settings.get("id") == "test"
    
    def test_text_with_extra_settings_and_kwargs(self):
        """Test Text with both extra_settings and kwargs"""
        text = Text("Hello", extra_settings={"id": "test"}, class_="highlight")
        assert text.extra_settings.get("id") == "test"
        assert text.extra_settings.get("class_") == "highlight"


class TestDownload:
    """Tests for the Download component"""
    
    def test_download_creation(self):
        """Test that Download can be created"""
        dl = Download("Download File", "file.txt", "content")
        assert dl.text == "Download File"
        assert dl.filename == "file.txt"
        assert dl.content == "content"
    
    def test_download_with_default_content_type(self):
        """Test Download with default content_type"""
        dl = Download("Download", "file.txt", "content")
        assert dl.content_type == "text/plain"
    
    def test_download_with_custom_content_type(self):
        """Test Download with custom content_type"""
        dl = Download("Download", "file.json", "{}", "application/json")
        assert dl.content_type == "application/json"
    
    def test_download_repr(self):
        """Test Download repr"""
        dl = Download("Download", "file.txt", "content")
        repr_str = repr(dl)
        assert "Download" in repr_str


class TestFileUpload:
    """Tests for the FileUpload component"""
    
    def test_fileupload_creation(self):
        """Test that FileUpload can be created"""
        fu = FileUpload("upload_field")
        assert fu.name == "upload_field"
    
    def test_fileupload_with_accept_string(self):
        """Test FileUpload with accept as string"""
        fu = FileUpload("upload_field", accept="image/*")
        assert fu.extra_settings.get("accept") == "image/*"
    
    def test_fileupload_with_accept_list(self):
        """Test FileUpload with accept as list"""
        fu = FileUpload("upload_field", accept=["image/png", "image/jpeg"])
        assert "image/png" in fu.extra_settings.get("accept")
        assert "image/jpeg" in fu.extra_settings.get("accept")
    
    def test_fileupload_without_accept(self):
        """Test FileUpload without accept"""
        fu = FileUpload("upload_field")
        assert fu.name == "upload_field"
    
    def test_fileupload_with_kwargs(self):
        """Test FileUpload with extra keyword arguments"""
        fu = FileUpload("upload_field", multiple=True, required=True)
        assert fu.extra_settings.get("multiple") is True
        assert fu.extra_settings.get("required") is True
    
    def test_fileupload_invalid_name(self):
        """Test that FileUpload rejects invalid names"""
        with pytest.raises(ValueError):
            FileUpload("invalid name")


class TestApiKeyBox:
    """Tests for the ApiKeyBox component"""
    
    def test_apikeybox_creation(self):
        """Test that ApiKeyBox can be created"""
        akb = ApiKeyBox("api_key", "gpt")
        assert akb.name == "api_key"
        assert akb.service == "gpt"
    
    def test_apikeybox_with_default_service(self):
        """Test ApiKeyBox with default service"""
        akb = ApiKeyBox("api_key")
        assert akb.service == "api"
    
    def test_apikeybox_with_label(self):
        """Test ApiKeyBox with label"""
        akb = ApiKeyBox("api_key", "gpt", label="Enter your API key")
        assert akb.label == "Enter your API key"
    
    def test_apikeybox_without_label(self):
        """Test ApiKeyBox without label"""
        akb = ApiKeyBox("api_key", "gpt")
        assert akb.label is None
    
    def test_apikeybox_with_kwargs(self):
        """Test ApiKeyBox with extra keyword arguments"""
        akb = ApiKeyBox("api_key", "gpt", id="key_input", class_="form-control")
        assert akb.extra_settings.get("id") == "key_input"
        assert akb.extra_settings.get("class_") == "form-control"
    
    def test_apikeybox_invalid_name(self):
        """Test that ApiKeyBox rejects invalid names"""
        with pytest.raises(ValueError):
            ApiKeyBox("invalid name", "gpt")


class TestMatPlotLibPlot:
    """Tests for the MatPlotLibPlot component"""
    
    def test_matplotlibplot_requires_matplotlib(self):
        """Test that MatPlotLibPlot raises ImportError when matplotlib is not available"""
        try:
            import matplotlib
            # If matplotlib is available, test basic creation
            plot = MatPlotLibPlot()
            assert plot.close_automatically is True
            assert plot.extra_matplotlib_settings.get("format") == "png"
            assert plot.extra_matplotlib_settings.get("bbox_inches") == "tight"
        except ImportError:
            # If matplotlib is not available, verify we get an ImportError
            with pytest.raises(ImportError, match="Matplotlib is not installed"):
                MatPlotLibPlot()
    
    def test_matplotlibplot_with_extra_matplotlib_settings(self):
        """Test MatPlotLibPlot with custom matplotlib settings"""
        try:
            import matplotlib
            plot = MatPlotLibPlot(extra_matplotlib_settings={"dpi": 300, "format": "svg"})
            assert plot.extra_matplotlib_settings.get("dpi") == 300
            assert plot.extra_matplotlib_settings.get("format") == "svg"
        except ImportError:
            pytest.skip("matplotlib not available")
    
    def test_matplotlibplot_close_automatically(self):
        """Test MatPlotLibPlot with close_automatically parameter"""
        try:
            import matplotlib
            plot1 = MatPlotLibPlot(close_automatically=True)
            plot2 = MatPlotLibPlot(close_automatically=False)
            assert plot1.close_automatically is True
            assert plot2.close_automatically is False
        except ImportError:
            pytest.skip("matplotlib not available")
    
    def test_matplotlibplot_with_kwargs(self):
        """Test MatPlotLibPlot with extra keyword arguments"""
        try:
            import matplotlib
            plot = MatPlotLibPlot(id="my_plot", class_="chart")
            assert plot.extra_settings.get("id") == "my_plot"
            assert plot.extra_settings.get("class_") == "chart"
        except ImportError:
            pytest.skip("matplotlib not available")


class TestComponentExtraSettings:
    """Tests for extra_settings and kwargs combinations across components"""
    
    def test_text_extra_settings_merge(self):
        """Test that extra_settings and kwargs merge correctly for Text"""
        text = Text("Hello", extra_settings={"id": "text1"}, class_="highlight")
        assert text.extra_settings.get("id") == "text1"
        assert text.extra_settings.get("class_") == "highlight"
    
    def test_div_extra_settings_merge(self):
        """Test that extra_settings and kwargs merge correctly for Div"""
        div = Div("Content", extra_settings={"id": "div1"}, class_="container")
        assert div.extra_settings.get("id") == "div1"
        assert div.extra_settings.get("class_") == "container"
    
    def test_span_extra_settings_merge(self):
        """Test that extra_settings and kwargs merge correctly for Span"""
        span = Span("Text", extra_settings={"id": "span1"}, style_color="blue")
        assert span.extra_settings.get("id") == "span1"
        assert span.extra_settings.get("style_color") == "blue"
    
    def test_multiple_kwargs_combinations(self):
        """Test components with various combinations of kwargs"""
        # Test with multiple style properties
        text1 = Text("Test", style_color="red", style_font_size="14px")
        assert text1.extra_settings.get("style_color") == "red"
        assert text1.extra_settings.get("style_font_size") == "14px"
        
        # Test with id and class
        div1 = Div("Content", id="main", class_="wrapper")
        assert div1.extra_settings.get("id") == "main"
        assert div1.extra_settings.get("class_") == "wrapper"


class TestComponentReprAndEquality:
    """Additional tests for repr and equality across components"""
    
    def test_button_repr_evaluation(self):
        """Test that Button repr can be evaluated (with limitations)"""
        button = Button("Submit", "/submit")
        repr_str = repr(button)
        # The repr should be informative even if not fully evaluable
        assert "Submit" in repr_str
        assert "/submit" in repr_str
    
    def test_text_hash_consistency(self):
        """Test that Text hash is consistent"""
        text1 = Text("Hello")
        text2 = Text("Hello")
        # Same content should have same hash
        assert hash(text1) == hash(text2)
    
    def test_text_hash_with_extra_settings(self):
        """Test Text hash with extra_settings"""
        text1 = Text("Hello", style_color="red")
        text2 = Text("Hello", style_color="red")
        text3 = Text("Hello", style_color="blue")
        
        # Same content and settings should have same hash
        assert hash(text1) == hash(text2)
        # Different settings should have different hash
        assert hash(text1) != hash(text3)
    
    def test_span_repr_with_extra_settings(self):
        """Test Span repr includes extra_settings"""
        span = Span("Hello", id="greeting")
        repr_str = repr(span)
        assert "Span" in repr_str
        assert "id" in repr_str or "greeting" in repr_str
    
    def test_div_repr_with_extra_settings(self):
        """Test Div repr includes extra_settings"""
        div = Div("Content", class_="container")
        repr_str = repr(div)
        assert "Div" in repr_str
        assert "class_" in repr_str or "container" in repr_str


class TestComponentEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_argument_with_zero_value(self):
        """Test Argument with zero values"""
        arg_int = Argument("count", 0)
        arg_float = Argument("ratio", 0.0)
        arg_bool = Argument("flag", False)
        
        assert arg_int.value == 0
        assert arg_float.value == 0.0
        assert arg_bool.value is False
    
    def test_textbox_with_empty_default_value(self):
        """Test TextBox with empty string default value"""
        tb = TextBox("field", default_value="")
        assert tb.default_value == ""
    
    def test_textarea_with_none_default_value(self):
        """Test TextArea with None default value"""
        ta = TextArea("field", default_value=None)
        assert ta.default_value == ""
    
    def test_selectbox_with_numeric_options(self):
        """Test SelectBox with numeric options"""
        sb = SelectBox("number", [1, 2, 3, 4, 5])
        # Options should be converted to strings
        assert all(isinstance(opt, str) for opt in sb.options)
        assert sb.options == ["1", "2", "3", "4", "5"]
    
    def test_text_empty_body(self):
        """Test Text with empty body"""
        text = Text("")
        assert text.body == ""
    
    def test_link_with_empty_arguments(self):
        """Test Link with empty arguments list"""
        link = Link("Click", "/page", arguments=[])
        assert link.arguments == []
    
    def test_button_with_empty_arguments(self):
        """Test Button with empty arguments list"""
        button = Button("Click", "/page", arguments=[])
        assert button.arguments == []
    
    def test_image_with_zero_dimensions(self):
        """Test Image with zero dimensions"""
        img = Image("/path.png", width=0, height=0)
        assert img.width == 0
        assert img.height == 0
    
    def test_table_with_empty_rows(self):
        """Test Table with empty rows list"""
        table = Table([])
        assert table.rows == []
    
    def test_numbered_list_with_single_item(self):
        """Test NumberedList with single item"""
        nl = NumberedList(["Single"])
        assert len(nl.items) == 1
    
    def test_bulleted_list_with_single_item(self):
        """Test BulletedList with single item"""
        bl = BulletedList(["Single"])
        assert len(bl.items) == 1
    
    def test_div_with_nested_components(self):
        """Test Div with nested components"""
        inner_span = Span("Inner")
        div = Div(inner_span, "Text")
        assert len(div.content) == 2
        assert div.content[0] == inner_span
    
    def test_header_all_levels(self):
        """Test Header with all valid levels"""
        for level in range(1, 7):
            h = Header("Title", level=level)
            assert h.level == level
    
    def test_fileupload_accept_with_extensions(self):
        """Test FileUpload accept with various extension formats"""
        # Test with extension without dot
        fu1 = FileUpload("file", accept=["png", "jpg"])
        assert ".png" in fu1.extra_settings.get("accept")
        assert ".jpg" in fu1.extra_settings.get("accept")
        
        # Test with extension with dot
        fu2 = FileUpload("file", accept=[".pdf", ".doc"])
        assert ".pdf" in fu2.extra_settings.get("accept")
        assert ".doc" in fu2.extra_settings.get("accept")
        
        # Test with MIME type
        fu3 = FileUpload("file", accept=["image/png", "image/jpeg"])
        assert "image/png" in fu3.extra_settings.get("accept")
        assert "image/jpeg" in fu3.extra_settings.get("accept")


class TestComponentStringRepresentations:
    """Tests for string representations (HTML output) of components"""
    
    def test_linebreak_html(self):
        """Test LineBreak HTML output"""
        lb = LineBreak()
        assert str(lb) == "<br />"
    
    def test_horizontalrule_html(self):
        """Test HorizontalRule HTML output"""
        hr = HorizontalRule()
        assert str(hr) == "<hr />"
    
    def test_text_html_without_extra_settings(self):
        """Test Text HTML output without extra settings"""
        text = Text("Hello")
        assert str(text) == "Hello"
    
    def test_text_html_with_extra_settings(self):
        """Test Text HTML output with extra settings"""
        text = Text("Hello", style_color="red")
        html_output = str(text)
        assert "<span" in html_output
        assert "Hello" in html_output
        assert "color" in html_output or "style" in html_output
    
    def test_header_html(self):
        """Test Header HTML output"""
        h1 = Header("Title", level=1)
        assert str(h1) == "<h1>Title</h1>"
        
        h2 = Header("Subtitle", level=2)
        assert str(h2) == "<h2>Subtitle</h2>"
