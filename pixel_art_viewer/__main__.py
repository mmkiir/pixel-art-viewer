from pathlib import Path
from typing import Optional

import wx
import wx.lib.inspection
import wx.lib.scrolledpanel


class ImagePanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)

        self.on_drag_start_mouse_position: Optional[wx.Point] = None

        self.image = wx.Image(100, 100)

        self.static_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(self.image))
        self.static_bitmap.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDownStaticBitmap)
        self.static_bitmap.Bind(wx.EVT_MOTION, self.OnMotionStaticBitmap)

        self.zoom = 1.0

        box_sizer = wx.BoxSizer()

        box_sizer.Add(self.static_bitmap, 1, wx.EXPAND)

        self.SetSizer(box_sizer)
        self.Layout()
        self.ShowScrollbars = True
        self.SetupScrolling()

        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnLeftDownStaticBitmap(self, event: wx.MouseEvent) -> None:
        event.ResumePropagation(2147483647)

    def OnLeftUpStaticBitmap(self, event: wx.MouseEvent) -> None:
        event.ResumePropagation(2147483647)

    def OnMotionStaticBitmap(self, event: wx.MouseEvent) -> None:
        event.ResumePropagation(2147483647)

    def OnLeftDown(self, event: wx.MouseEvent) -> None:
        self.on_drag_start_mouse_position = event.GetPosition()

    def OnLeftUp(self, event: wx.MouseEvent) -> None:
        self.on_drag_start_mouse_position = None

    def OnMotion(self, event: wx.MouseEvent) -> None:
        if not (event.Dragging() and event.LeftIsDown()):
            return

        mouse_position: wx.Point = event.GetPosition()
        mouse_delta: wx.Point = mouse_position - self.on_drag_start_mouse_position

        old_scroll_horizontal: int = self.GetScrollPos(wx.HORIZONTAL)
        old_scroll_vertical: int = self.GetScrollPos(wx.VERTICAL)

        new_scroll_horizontal: int = (
            old_scroll_horizontal - mouse_delta.x // self.GetScrollPixelsPerUnit()[0]
        )
        new_scroll_vertical: int = (
            old_scroll_vertical - mouse_delta.y // self.GetScrollPixelsPerUnit()[1]
        )

        self.Scroll(new_scroll_horizontal, new_scroll_vertical)

        event.Skip()

    def SetImage(self, image: wx.Image) -> None:
        self.image = image
        self.static_bitmap.SetBitmap(wx.Bitmap(self.image))
        self.zoom = 1.0
        self.ZoomToFit()

    def OnMouseWheel(self, event: wx.Event) -> None:
        delta = 0.1 * event.GetWheelRotation() / event.GetWheelDelta()
        self.zoom = max(1.0, self.zoom + delta)
        self.ZoomToFit()

    def ZoomToFit(self) -> None:

        width, height = self.GetSize()

        image_aspect_ratio = self.image.Width / self.image.Height

        if width * image_aspect_ratio < height:
            new_image_width = width
            new_image_height = width / image_aspect_ratio
        else:
            new_image_width = height * image_aspect_ratio
            new_image_height = height

        new_zoomed_image_width = new_image_width * self.zoom
        new_zoomed_image_height = new_image_height * self.zoom

        scroll_h: int = self.GetScrollPos(wx.HORIZONTAL)
        scroll_v: int = self.GetScrollPos(wx.VERTICAL)

        image = self.image.Scale(new_zoomed_image_width, new_zoomed_image_height)
        self.static_bitmap.SetBitmap(wx.Bitmap(image))

        self.Layout()
        self.SetupScrolling()
        self.Scroll(scroll_h, scroll_v)  # FIXME: Scrolls back to (0,0).

    def OnSize(self, _) -> None:
        self.ZoomToFit()


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)

        self.is_dark_background: bool = False

        self.current_file: Optional[str] = None
        self.current_dir: Optional[str] = None

        file_menu: wx.Menu = wx.Menu()

        open_menu_item: wx.MenuItem = wx.MenuItem(file_menu, wx.ID_OPEN, "&Open...")
        self.Bind(wx.EVT_MENU, self.OnOpen, open_menu_item)
        file_menu.Append(open_menu_item)

        file_menu.AppendSeparator()

        exit_menu_item: wx.MenuItem = wx.MenuItem(file_menu, wx.ID_EXIT, "Exit")
        self.Bind(wx.EVT_MENU, self.OnExit, exit_menu_item)
        file_menu.Append(exit_menu_item)

        menu_bar: wx.MenuBar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")

        self.SetMenuBar(menu_bar)

        button_panel = wx.Panel(self)
        button_grid_sizer = wx.GridSizer(5)

        self.previous_button = wx.Button(button_panel, style=wx.BU_NOTEXT)
        self.previous_button.SetBitmap(
            wx.Bitmap(
                wx.Image(
                    str(
                        Path.cwd() / "assets" / "Tinycons_Pixel_Art_Viewer_Previous.png"
                    )
                ).Scale(32, 32)
            )
        )
        self.previous_button.Bind(wx.EVT_LEFT_DOWN, self.OnPrevious)

        self.next_button = wx.Button(button_panel, style=wx.BU_NOTEXT)
        self.next_button.SetBitmap(
            wx.Bitmap(
                wx.Image(
                    str(Path.cwd() / "assets" / "Tinycons_Pixel_Art_Viewer_Next.png")
                ).Scale(32, 32)
            )
        )
        self.next_button.Bind(wx.EVT_LEFT_DOWN, self.OnNext)

        zoom_to_fit_button = wx.Button(button_panel, style=wx.BU_NOTEXT)
        zoom_to_fit_button.SetBitmap(
            wx.Bitmap(
                wx.Image(
                    str(
                        Path.cwd()
                        / "assets"
                        / "Tinycons_Pixel_Art_Viewer_Zoom_To_Fit.png"
                    )
                ).Scale(32, 32)
            )
        )
        zoom_to_fit_button.Bind(wx.EVT_LEFT_DOWN, self.OnZoomToFit)

        preview_button = wx.Button(button_panel, style=wx.BU_NOTEXT)
        preview_button.SetBitmap(
            wx.Bitmap(
                wx.Image(
                    str(Path.cwd() / "assets" / "Tinycons_Pixel_Art_Viewer_Preview.png")
                ).Scale(32, 32)
            )
        )
        # TODO: Implement 1:1 preview.

        switch_background_button = wx.Button(button_panel, style=wx.BU_NOTEXT)
        switch_background_button.SetBitmap(
            wx.Bitmap(
                wx.Image(
                    str(
                        Path.cwd()
                        / "assets"
                        / "Tinycons_Pixel_Art_Viewer_Switch_Background.png"
                    )
                ).Scale(32, 32)
            )
        )
        switch_background_button.Bind(wx.EVT_LEFT_DOWN, self.OnSwitchBackground)

        button_grid_sizer.Add(self.previous_button, 1, wx.EXPAND)
        button_grid_sizer.Add(switch_background_button, 1, wx.EXPAND)
        button_grid_sizer.Add(zoom_to_fit_button, 1, wx.EXPAND)
        button_grid_sizer.Add(preview_button, 1, wx.EXPAND)
        button_grid_sizer.Add(self.next_button, 1, wx.EXPAND)

        button_panel.SetSizer(button_grid_sizer)
        button_panel.Layout()

        self.image_panel = ImagePanel(self)

        box_sizer = wx.BoxSizer(wx.VERTICAL)

        box_sizer.Add(self.image_panel, 1, wx.EXPAND)
        box_sizer.Add(button_panel, 0, wx.EXPAND)

        self.SetTitle("Pixel Art Viewer")

        self.SetSizer(box_sizer)
        self.Layout()
        self.Show()

    def OnZoomToFit(self, _) -> None:
        self.image_panel.zoom = 1.0
        self.image_panel.ZoomToFit()

    def OnNext(self, _) -> None:
        paths = list(self.parent.glob("*.png"))
        self.LoadFile(str(paths[paths.index(self.parent / self.name) + 1]))

    def OnPrevious(self, _) -> None:
        paths = list(self.parent.glob("*.png"))
        self.LoadFile(str(paths[paths.index(self.parent / self.name) - 1]))

    def OnSwitchBackground(self, _) -> None:
        if self.is_dark_background:
            self.SetBackgroundColour(wx.WHITE)
            self.is_dark_background = False
        else:
            self.SetBackgroundColour(wx.BLACK)
            self.is_dark_background = True

        self.Layout()

    def LoadFile(self, name: str) -> None:
        path = Path(name)

        if not path.exists():
            return

        self.parent = path.parent
        self.name = path.name

        self.image_panel.SetImage(wx.Image(str(self.parent / self.name)))

        self.SetTitle(self.name)

        self.UpdateButtonStates()

    def OnOpen(self, name: str) -> None:
        with wx.FileDialog(self, "Open...", style=wx.FD_SAVE) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            self.LoadFile(file_dialog.GetPath())

    def OnExit(self, name: str) -> None:
        self.Close()

    def UpdateButtonStates(self) -> None:
        paths = list(self.parent.glob("*.png"))

        if paths.index(self.parent / self.name) == 0:
            self.previous_button.Disable()
        else:
            self.previous_button.Enable()

        if paths.index(self.parent / self.name) == len(paths) - 1:
            self.next_button.Disable()
        else:
            self.next_button.Enable()


app = wx.App()

# wx.lib.inspection.InspectionTool().Show()

frame = MainFrame(None)


app.MainLoop()
