from customtkinter import CTkFrame
from editing_tools import JSONEditor

SETTINGS_FILE_PATH = 'settings.json'

settings_file = JSONEditor(json_file_path=SETTINGS_FILE_PATH)
settings_contents = settings_file.get_json_data()

class PrimaryFrame(CTkFrame):
    def __init__(self, application_frame: CTkFrame):
        super().__init__(
            master=application_frame,
            width=550,
            height=350,
            fg_color='#000000',
            border_color=['#f5c1d9', '#edb1cb'],
            border_width=4,
            corner_radius=0
        )

        self.thumbnail_frame = ThumbnailFrame(master=self)
        self.thumbnail_frame.place(anchor='center', relx=0.181, rely=0.47)

        self.title_frame = TitleFrame(master=self)
        self.title_frame.place(anchor='center', relx=0.601, rely=0.35)

        self.secondary_frame = SecondaryFrame(master=self)
        self.secondary_frame.place(anchor='center', relx=0.601, rely=0.5)


class ThumbnailFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(
            master=master,
            width=125,
            height=125,
            corner_radius=0,
            fg_color=['#8a031e', '#ed003a'],
            border_color=['#4e4e50', '#8f9095'],
            border_width=4
        )


class TitleFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(
            master=master,
            width=344.31,
            height=40,
            fg_color='#000000',
            border_width=4,
            corner_radius=0,
            border_color=['#4e4e50', '#8f9095']
        )


class SecondaryFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(
            master=master,
            fg_color='#000000',
            width=344.31,
            height=104,
            border_width=4,
            corner_radius=0,
            border_color=['#4e4e50', '#8f9095']
        )


if __name__ == '__main__':
    pass
