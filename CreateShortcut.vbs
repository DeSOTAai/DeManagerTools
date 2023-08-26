Set oWS = WScript.CreateObject("WScript.Shell") 
sLinkFile = "C:\Users\franc\Desktop\Desota - Manager Tools.lnk" 
Set oLink = oWS.CreateShortcut(sLinkFile) 
oLink.TargetPath = "C:\Users\franc\Desota\DeManagerTools\dist\Desota - Manager Tools\Desota - Manager Tools.exe"  
oLink.Save 
