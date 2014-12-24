# -*- coding: UTF-8 -*-
'''
Created on 2014年11月22日

@author: Administrator
'''

import wx
from SwitchModule import SqlSwitch, XmlSwitch

class ToolBoxFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title=u"工具箱", size=(640,480))
        statBar = self.CreateStatusBar()
        self.tabPanel = wx.Notebook(self)
        
        pageSqlSwitch = SqlSwitch(self.tabPanel, statBar)
        self.tabPanel.AddPage(pageSqlSwitch, u"Sql语句转换", True)
        
        pageXmlSwitch = XmlSwitch(self.tabPanel, statBar)
        self.tabPanel.AddPage(pageXmlSwitch, u"Xml语句转换")

if __name__ == "__main__":
    app = wx.App(False)
    frame = ToolBoxFrame()
    frame.Show()
    app.MainLoop()
