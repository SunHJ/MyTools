# -*- coding: UTF-8 -*-
'''
Created on 2014年11月22日

@author: Administrator
'''
import wx
import re

class SwitchTemplate(wx.Panel):
    def __init__(self, parent, statBar):
        wx.Panel.__init__(self, parent)
        lbinput = wx.StaticText(self, label=u"输入要转换的字符串：")
        self.srcText = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH|wx.HSCROLL)
        self.srcText.SetMaxLength(0)
        switchBtn = wx.Button(self, label=u"转换")
        switchBtn.Bind(wx.EVT_BUTTON, self.onSwitch)
        self.desText = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        self.desText.SetMaxLength(0)
        copyBtn = wx.Button(self, label=u"复制到粘贴板")
        copyBtn.Bind(wx.EVT_BUTTON, self.onCopy)
 
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(lbinput, 0, wx.ALL, 5)
        sizer.Add(self.srcText, 1, wx.EXPAND)
        sizer.Add(switchBtn, 0, wx.ALL|wx.CENTER, 5)
        sizer.Add(self.desText, 1, wx.EXPAND)
        sizer.Add(copyBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(sizer)
        
        self.statusBar = statBar
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
    
    def doAction(self, srcStr):
        print(u"The function 'doAction' not define")
        assert(False)
        
    def onSwitch(self, event):
        if self.srcText.IsEmpty():
            wx.MessageBox(u"没有输入转换个蛋啊!")
            return
        
        self.desText.Clear()
        nLines = self.srcText.GetNumberOfLines()
        for idx in range(nLines):
            strLine = self.srcText.GetLineText(idx)
            if strLine:
                newline = self.doAction(strLine)
                self.desText.AppendText('%s\n' % newline)

    def onCopy(self, event):
        self.dataObj = wx.TextDataObject()
        self.dataObj.SetText(self.desText.GetValue())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(self.dataObj)
            wx.TheClipboard.Close()
            self.statusBar.SetStatusText(u"转换结果已复制到粘贴板", 0)
            self.timer.Start(1500)
        else:
            wx.MessageBox(u"Unable to open the clipboard", "Error")
            
    def OnTimer(self, event):
        self.statusBar.SetStatusText("", 0)

class SqlSwitch(SwitchTemplate):
    def __init__(self, parent, statBar):
        SwitchTemplate.__init__(self, parent, statBar)
        
    def doAction(self, srcStr):
        reStr = ""
        if srcStr:
            reStr = 'sql.append(" %s");' % srcStr
        return reStr

class XmlSwitch(SwitchTemplate):
    def __init__(self, parent, statBar):
        SwitchTemplate.__init__(self, parent, statBar)
        
        # <name>?</name>
        reg = r'(\s*)<\s*(\w+)\s*>(.*?)<\s*/\s*(\2)\s*>'
        self.rePattern1 = re.compile(reg)
        # <name />
        reg = r'(\s*)<\s*(\w+)\s*/\s*>'
        self.rePattern2 = re.compile(reg)
    
    def doAction(self, srcStr):
        reStr = ""
        if srcStr:
            if self.rePattern1.match(srcStr):
                reStr = self.rePattern1.sub(r'\1<\2>A</\4>', srcStr)
            elif self.rePattern2.match(srcStr):
                reStr = self.rePattern2.sub(r'\1<\2>A</\2>', srcStr)
            else:
                reStr = srcStr
        return reStr

if __name__ == "__main__":
    app = wx.App(False)
    frame = wx.Frame(None, title=u"XML语句格式化", size=(640,480))
    statBar = frame.CreateStatusBar()
    XmlSwitch(frame, statBar)
#     SqlSwitch(frame, statBar)
    frame.Show()
    app.MainLoop()
