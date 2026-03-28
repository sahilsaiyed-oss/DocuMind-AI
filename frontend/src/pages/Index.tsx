import { useState, useRef, useEffect, useCallback } from "react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import TypingIndicator from "@/components/TypingIndicator";
import AppHeader from "@/components/AppHeader";
import KnowledgeSidebar from "@/components/KnowledgeSidebar";
import { Brain, Upload, FolderOpen, RefreshCcw, Trash2, Edit3, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

interface Message {
  id: string; role: "user" | "ai"; content: string;
  sources?: { name: string }[]; filter?: string;
}

const API_BASE = "http://localhost:8000/api/v1";

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);
  const [activeCategory, setActiveCategory] = useState("All");
  const [totalQueries, setTotalQueries] = useState(0);
  
  // States for Inputs
  const [localFolderPath, setLocalFolderPath] = useState("");
  const [bulkCategoryTag, setBulkCategoryTag] = useState("general"); // BACK AGAIN!

  const scrollRef = useRef<HTMLDivElement>(null);

  const refreshData = async () => {
    try {
      const listRes = await fetch(`${API_BASE}/documents/list`);
      const listData = await listRes.json();
      setCategories(listData.categories || []);

      const anaRes = await fetch(`${API_BASE}/analytics/summary`);
      const anaData = await anaRes.json();
      setTotalQueries(anaData.total_questions_handled || 0);
    } catch (err) { console.error("Sync Error"); }
  };

  useEffect(() => { refreshData(); }, []);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    const match = text.match(/"([^"]+)"/);
    if (match) setActiveCategory(match[1]);

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: text,
      });
      const data = await res.json();
      
      const rawSources = data.sources || [];
      const uniqueSourceNames = Array.from(new Set(rawSources.map((s: any) => s.filename.split('\\').pop().split('/').pop())));

      const aiMsg: Message = {
        id: crypto.randomUUID(), role: "ai",
        content: data.answer,
        sources: uniqueSourceNames.map(name => ({ name: name as string }))
      };
      setMessages((prev) => [...prev, aiMsg]);
      refreshData();
    } catch (err) { toast.error("AI connection lost"); }
    finally { setLoading(false); }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const cat = prompt("Category tag for this file?", activeCategory === "All" ? "general" : activeCategory);
    if (!cat) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", cat);

    toast.info("Training AI on this file...");
    try {
      const res = await fetch(`${API_BASE}/ingest/file`, { method: "POST", body: formData });
      if (res.ok) { toast.success("File Ingested!"); refreshData(); }
    } catch (err) { toast.error("Upload Fail"); }
  };

  const handleRename = async () => {
    if (activeCategory === "All") return;
    const newName = prompt(`Rename category '${activeCategory}' to:`, activeCategory);
    if (!newName || newName === activeCategory) return;

    try {
      const res = await fetch(`${API_BASE}/documents/rename?old_name=${activeCategory}&new_name=${newName}`, { method: 'POST' });
      if (res.ok) {
        toast.success("Category Renamed!");
        setActiveCategory(newName);
        refreshData();
      }
    } catch (err) { toast.error("Rename Failed"); }
  };

  const handleDelete = async () => {
    if (activeCategory === "All") return;
    if (!confirm(`Delete all data in '${activeCategory}'?`)) return;
    
    try {
      await fetch(`${API_BASE}/documents/category/${activeCategory}`, { method: 'DELETE' });
      toast.success("Category Deleted!");
      setActiveCategory("All");
      refreshData();
    } catch (err) { toast.error("Delete Failed"); }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      <KnowledgeSidebar
        domains={categories.map(c => c.name)}
        activeCategory={activeCategory}
        totalQueries={totalQueries}
        onSelectDomain={(d) => setActiveCategory(d)}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <AppHeader onToggleSidebar={() => setSidebarOpen(true)} />
        
        {/* --- MAIN ACTION BAR --- */}
        <div className="px-6 py-3 border-b border-border/40 bg-card/10 backdrop-blur-md">
            <div className="flex flex-wrap items-center justify-between gap-4">
                
                {/* 1. BULK FOLDER SECTION (RESTORED CATEGORY BOX) */}
                <div className="flex items-center gap-2 bg-secondary/30 p-1 rounded-lg border border-border/50 flex-1 max-w-2xl">
                    <FolderOpen size={16} className="ml-2 text-primary" />
                    <input 
                        type="text" placeholder="Folder Path..." 
                        className="bg-transparent border-none px-2 py-1 text-xs flex-1 outline-none"
                        value={localFolderPath} onChange={(e) => setLocalFolderPath(e.target.value)}
                    />
                    <div className="h-4 w-[1px] bg-border mx-1"></div>
                    <input 
                        type="text" placeholder="Tag Name" 
                        className="bg-transparent border-none px-2 py-1 text-xs w-24 outline-none font-bold text-primary"
                        value={bulkCategoryTag} onChange={(e) => setBulkCategoryTag(e.target.value)}
                    />
                    <button onClick={async () => {
                        if(!localFolderPath) return toast.error("Path likho!");
                        toast.info("Bulk training started...");
                        const res = await fetch(`${API_BASE}/ingest/folder?folder_path=${encodeURIComponent(localFolderPath)}&category=${bulkCategoryTag}`, {method:'POST'});
                        if (res.ok) { toast.success("Folder Synced!"); refreshData(); setLocalFolderPath(""); }
                    }} className="bg-primary text-primary-foreground px-3 py-1 rounded-md text-[11px] font-black uppercase tracking-tighter hover:scale-105 transition-all">Bulk Train</button>
                </div>

                {/* 2. CATEGORY MANAGEMENT & FILE UPLOAD */}
                <div className="flex items-center gap-2">
                    {activeCategory !== "All" && (
                        <div className="flex items-center gap-1 bg-secondary/50 px-2 py-1 rounded-lg border border-border">
                            <span className="text-[10px] font-bold text-muted-foreground mr-2 uppercase">Manage {activeCategory}:</span>
                            <button onClick={handleRename} className="p-1.5 hover:bg-primary/20 text-primary rounded-md transition-all" title="Rename Folder"><Edit3 size={14}/></button>
                            <button onClick={handleDelete} className="p-1.5 hover:bg-destructive/20 text-destructive rounded-md transition-all" title="Delete Folder"><Trash2 size={14}/></button>
                        </div>
                    )}
                    
                    <label className="flex items-center gap-2 cursor-pointer bg-primary/10 text-primary border border-primary/30 px-4 py-1.5 rounded-lg text-xs font-bold hover:bg-primary hover:text-white transition-all">
                        <Upload size={14} />
                        <span>Upload File</span>
                        <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf,.txt,.docx" />
                    </label>

                    <button onClick={refreshData} className="p-2 hover:bg-secondary rounded-full border border-border" title="Refresh Everything"><RefreshCcw size={14}/></button>
                </div>
            </div>
        </div>

        {/* --- CHAT VIEW --- */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 scrollbar-hide">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="relative mb-6">
                <div className="absolute -inset-4 bg-primary/20 blur-xl rounded-full animate-pulse"></div>
                <Brain size={80} className="relative text-primary" />
              </div>
              <h2 className="text-4xl font-black tracking-tighter mb-2">DocuMind AI <span className="text-primary text-sm font-normal border border-primary px-2 py-0.5 rounded-full ml-2 uppercase">Pro</span></h2>
              <p className="text-muted-foreground text-sm max-w-sm">Ready to analyze your knowledge domains. Select a folder to begin.</p>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-10">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} role={msg.role} content={msg.content} sources={msg.sources} />
              ))}
              {loading && <TypingIndicator />}
            </div>
          )}
        </div>

        {/* --- BOTTOM INPUT --- */}
        <div className="p-6 bg-gradient-to-t from-background via-background to-transparent border-t border-border/20">
            <div className="max-w-4xl mx-auto relative">
                <div className="absolute -top-8 left-0 flex items-center gap-2">
                    <ShieldCheck size={12} className="text-primary" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">
                        Connected to: <span className="text-primary underline">{activeCategory}</span>
                    </span>
                </div>
                <ChatInput 
                    onSend={(val) => {
                        const finalQuery = activeCategory !== "All" && !val.includes(`"${activeCategory}"`) 
                            ? `${val} "${activeCategory}"` 
                            : val;
                        handleSend(finalQuery);
                    }} 
                    disabled={loading} 
                />
            </div>
        </div>
      </div>
    </div>
  );
};

export default Index;