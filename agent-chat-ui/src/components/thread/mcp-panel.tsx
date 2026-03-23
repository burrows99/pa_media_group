import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "../ui/sheet";
import { Button } from "../ui/button";
import Editor from "@monaco-editor/react";
import { Save, Server, Trash2, Wrench, RefreshCw, CheckSquare, Square, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { createClient } from "@/providers/client";

interface McpPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DEFAULT_JSON = `{
  "mcpServers": {
    "sample-server": {
      "command": "uvx",
      "args": ["mcp-server-sample"]
    }
  }
}`;

export function McpPanel({ open, onOpenChange }: McpPanelProps) {
  const [jsonConfig, setJsonConfig] = useState(DEFAULT_JSON);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState<"list" | "json">("list");

  const [mcpTools, setMcpTools] = useState<Record<string, any[]>>({});
  const [loadingTools, setLoadingTools] = useState<Record<string, boolean>>({});
  const [toolErrors, setToolErrors] = useState<Record<string, string>>({});
  const [disabledToolsMap, setDisabledToolsMap] = useState<Record<string, string[]>>({});
  const [collapsedToolsMap, setCollapsedToolsMap] = useState<Record<string, boolean>>({});

  const toggleCollapse = (serverName: string) => {
     setCollapsedToolsMap((prev: Record<string, boolean>) => ({...prev, [serverName]: !prev[serverName]}));
  };

  useEffect(() => {
    try {
      const dt = localStorage.getItem("mcp_disabled_tools");
      if (dt) setDisabledToolsMap(JSON.parse(dt));
    } catch(e) {}
    
    if (open) {
       const saved = localStorage.getItem("mcp_servers_config");
       if (saved) {
         setJsonConfig(saved);
       } else {
         const oldSaved = localStorage.getItem("mcp_servers");
         if (oldSaved) {
            try {
              const oldArray = JSON.parse(oldSaved);
              if (Array.isArray(oldArray) && oldArray.length > 0) {
                 const newFormat: any = { mcpServers: {} };
                 oldArray.forEach((s: any) => {
                    newFormat.mcpServers[s.name || "unnamed"] = {
                        command: s.command,
                        args: s.args || []
                    };
                 });
                 setJsonConfig(JSON.stringify(newFormat, null, 2));
              }
            } catch (e) {}
         }
       }
       setError(null);
       setSuccess(false);
    }
  }, [open]);

  const handleSave = () => {
    try {
        const parsed = JSON.parse(jsonConfig);
        if (!parsed || typeof parsed !== "object" || !parsed.mcpServers) {
            throw new Error('Configuration must be a valid JSON object containing "mcpServers".');
        }
        
        const formatted = JSON.stringify(parsed, null, 2);
        localStorage.setItem("mcp_servers_config", formatted);
        setJsonConfig(formatted);
        setError(null);
        setSuccess(true);
        setTimeout(() => setSuccess(false), 2000);
    } catch (e: any) {
        setError(e.message || "Invalid JSON formatting.");
        setSuccess(false);
    }
  };

  const removeServer = (name: string) => {
     try {
       const parsed = JSON.parse(jsonConfig);
       if (parsed && parsed.mcpServers && parsed.mcpServers[name]) {
          delete parsed.mcpServers[name];
          const newJson = JSON.stringify(parsed, null, 2);
          setJsonConfig(newJson);
          localStorage.setItem("mcp_servers_config", newJson);
       }
     } catch (e) {}
  };

  const toggleTool = (serverName: string, toolName: string) => {
     setDisabledToolsMap((prev: any) => {
         const disabled = prev[serverName] || [];
         let newDisabled;
         if (disabled.includes(toolName)) {
             newDisabled = disabled.filter((t: string) => t !== toolName);
         } else {
             newDisabled = [...disabled, toolName];
         }
         const newState = { ...prev, [serverName]: newDisabled };
         localStorage.setItem("mcp_disabled_tools", JSON.stringify(newState));
         return newState;
     });
  };

  let serversArray: Array<{name: string, config: any}> = [];
  try {
     const parsed = JSON.parse(jsonConfig);
     if (parsed?.mcpServers) {
         serversArray = Object.entries(parsed.mcpServers).map(([name, conf]: [string, any]) => ({
             name,
             config: conf
         }));
     }
  } catch (e) {}

  const fetchTools = async (serverName: string, config: any) => {
      setLoadingTools((prev: any) => ({...prev, [serverName]: true}));
      setToolErrors((prev: any) => ({...prev, [serverName]: ""}));
      try {
          // @ts-ignore: NextJS process.env typing might be missing in some setups
          const apiUrl = process.env.NEXT_PUBLIC_LANGGRAPH_API_URL || "http://localhost:2024";
          const client = createClient(apiUrl, undefined, undefined);
          const res = await client.runs.wait(undefined, "mcp_tools", {
             input: {
                 mcp_servers_config: {
                     [serverName]: config
                 }
             }
          });
          const tools = res?.tools || res?.values?.tools || (res as any)?.outputs?.tools || (Array.isArray(res) ? res[0]?.tools || res[0]?.values?.tools : undefined);
          if (tools) {
             setMcpTools((prev: any) => ({...prev, [serverName]: tools}));
          } else {
             setToolErrors((prev: any) => ({...prev, [serverName]: "No tools returned"}));
          }
      } catch (e: any) {
          setToolErrors((prev: any) => ({...prev, [serverName]: e.message || "Fetch failed"}));
      } finally {
          setLoadingTools((prev: any) => ({...prev, [serverName]: false}));
      }
  };

  useEffect(() => {
      if (open && activeTab === "list") {
          serversArray.forEach(s => {
              if (!mcpTools[s.name] && typeof loadingTools[s.name] === "undefined") {
                  fetchTools(s.name, s.config);
              }
          });
      }
  }, [open, activeTab, jsonConfig]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto p-8 flex flex-col h-full bg-white">
        <SheetHeader className="p-0 pb-2 shrink-0">
          <SheetTitle>MCP Servers Configuration</SheetTitle>
          <SheetDescription>
            Manage your Model Context Protocol (MCP) tool servers.
          </SheetDescription>
        </SheetHeader>
        
        <div className="flex border-b mt-2 shrink-0">
          <button 
            onClick={() => setActiveTab("list")} 
            className={cn("px-4 py-2.5 font-medium text-sm border-b-2 transition-colors", activeTab === "list" ? "border-black text-black" : "border-transparent text-gray-500 hover:text-gray-800")}
          >
             Connected Servers
          </button>
          <button 
            onClick={() => setActiveTab("json")} 
            className={cn("px-4 py-2.5 font-medium text-sm border-b-2 transition-colors", activeTab === "json" ? "border-black text-black" : "border-transparent text-gray-500 hover:text-gray-800")}
          >
             JSON Config
          </button>
        </div>

        <div className="mt-4 flex flex-col gap-4 flex-1 overflow-y-auto pr-2">
          {activeTab === "list" && (
             <div className="flex flex-col gap-4">
               {serversArray.length === 0 ? (
                  <div className="flex flex-col items-center justify-center p-8 text-center bg-gray-50 rounded-lg border border-dashed">
                      <p className="text-sm text-gray-500 mb-2">No servers configured.</p>
                      <Button variant="outline" size="sm" onClick={() => setActiveTab("json")}>Edit JSON to add one</Button>
                  </div>
               ) : (
                  serversArray.map((server, idx) => (
                    <div key={idx} className="flex flex-col p-4 rounded-lg border shadow-sm text-sm bg-white">
                      <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                        <div className="flex items-center gap-3.5 min-w-0 flex-1">
                          <div className="p-2 bg-gray-100 rounded-md shrink-0">
                             <Server className="size-5 text-gray-600" />
                          </div>
                          <div className="min-w-0 flex flex-col items-start pr-2 w-full">
                            <p className="font-semibold text-gray-900 truncate w-full">{server.name}</p>
                            <p 
                               className="text-xs text-gray-500 mt-1 font-mono bg-gray-50 px-1.5 py-0.5 rounded border truncate max-w-full"
                               title={server.config.type === "http" || server.config.type === "sse" ? server.config.url : `${server.config.command} ${(server.config.args || []).join(" ")}`}
                            >
                               {server.config.type === "http" || server.config.type === "sse" ? server.config.url : `${server.config.command} ${(server.config.args || []).join(" ")}`}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" onClick={() => fetchTools(server.name, server.config)} className="text-gray-400 hover:text-blue-600 hover:bg-blue-50" title="Refresh Tools">
                            <RefreshCw className={cn("size-4", loadingTools[server.name] && "animate-spin")} />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => removeServer(server.name)} className="text-red-400 hover:text-red-700 hover:bg-red-50" title="Remove Server">
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="mt-3">
                         <h4 
                           className="flex items-center gap-1.5 text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide cursor-pointer hover:text-gray-900 transition-colors select-none"
                           onClick={() => toggleCollapse(server.name)}
                         >
                            {collapsedToolsMap[server.name] ? <ChevronRight className="size-3" /> : <ChevronDown className="size-3" />}
                            <Wrench className="size-3" /> Tools
                            {mcpTools[server.name] && <span className="ml-auto text-[10px] bg-gray-100 px-1.5 py-0.5 rounded text-gray-500">{mcpTools[server.name].length}</span>}
                         </h4>
                         
                         {!collapsedToolsMap[server.name] && (
                           <>
                             {loadingTools[server.name] && !mcpTools[server.name] ? (
                                <p className="text-xs text-gray-400 italic">Connecting and extracting tools...</p>
                             ) : toolErrors[server.name] ? (
                                <p className="text-xs text-red-500 bg-red-50 p-2 rounded-md border border-red-100">{toolErrors[server.name]}</p>
                             ) : mcpTools[server.name] && mcpTools[server.name].length > 0 ? (
                                <div className="flex flex-col gap-1.5">
                                   {mcpTools[server.name].map((tool: any) => {
                                      const disabled = disabledToolsMap[server.name] || [];
                                      const isEnabled = !disabled.includes(tool.name);
                                      return (
                                        <button 
                                          key={tool.name} 
                                          className={cn("flex items-start text-left gap-2 p-2 rounded-md transition-colors", isEnabled ? "bg-slate-50 hover:bg-slate-100" : "opacity-60 hover:opacity-100")}
                                          onClick={() => toggleTool(server.name, tool.name)}
                                        >
                                           <div className="mt-0.5 shrink-0">
                                             {isEnabled ? <CheckSquare className="size-4 text-blue-600" /> : <Square className="size-4 text-gray-400" />}
                                           </div>
                                           <div className="flex flex-col">
                                              <span className={cn("font-medium text-sm", isEnabled ? "text-slate-900" : "text-gray-500")}>{tool.name}</span>
                                              {tool.description && <span className="text-xs text-gray-500 line-clamp-1 mt-0.5" title={tool.description}>{tool.description}</span>}
                                           </div>
                                        </button>
                                      );
                                   })}
                                </div>
                             ) : (
                                <p className="text-xs text-gray-400 italic">No tools provided by this server.</p>
                             )}
                           </>
                         )}
                      </div>
                    </div>
                  ))
               )}
             </div>
          )}

          {activeTab === "json" && (
             <div className="flex flex-col h-full">
               <div className="flex-1 min-h-[400px] h-full border border-slate-200 rounded-md overflow-hidden bg-white">
                 <Editor
                   height="100%"
                   language="json"
                   value={jsonConfig}
                   onChange={(value: string | undefined) => setJsonConfig(value || "")}
                   options={{
                     minimap: { enabled: false },
                     scrollBeyondLastLine: false,
                     wordWrap: "on",
                     formatOnPaste: true,
                     tabSize: 2,
                   }}
                 />
               </div>
               {error && <p className="text-sm text-red-500 font-medium mt-3">{error}</p>}
               <Button onClick={handleSave} className="w-full gap-2 transition-all mt-4" variant={success ? "secondary" : "default"}>
                  <Save className="size-4" /> 
                  {success ? "Configuration Saved!" : "Save Configuration"}
               </Button>
             </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
