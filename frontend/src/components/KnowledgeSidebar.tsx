import { Brain, FolderOpen, Activity, MessageSquare, X } from "lucide-react";

interface KnowledgeSidebarProps {
  domains: string[];
  activeCategory: string | null;
  totalQueries: number;
  onSelectDomain: (domain: string) => void;
  open: boolean;
  onClose: () => void;
}

const KnowledgeSidebar = ({
  domains,
  activeCategory,
  totalQueries,
  onSelectDomain,
  open,
  onClose,
}: KnowledgeSidebarProps) => (
  <>
    {/* Mobile overlay */}
    {open && (
      <div className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40 lg:hidden" onClick={onClose} />
    )}

    <aside
      className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-300 ${
        open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      }`}
    >
      {/* Logo */}
      <div className="h-14 flex items-center justify-between px-5 border-b border-sidebar-border flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <Brain className="w-4 h-4 text-primary" />
          </div>
          <span className="font-semibold text-sm text-sidebar-accent-foreground">DocuMind AI</span>
        </div>
        <button onClick={onClose} className="lg:hidden w-7 h-7 rounded-md hover:bg-sidebar-accent flex items-center justify-center">
          <X className="w-4 h-4 text-sidebar-foreground" />
        </button>
      </div>

      {/* Domains */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-1">
        <p className="text-[11px] font-medium uppercase tracking-wider text-sidebar-foreground/50 px-2 mb-2">
          Knowledge Domains
        </p>
        {domains.map((d) => (
          <button
            key={d}
            onClick={() => onSelectDomain(d)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all duration-200 ${
              activeCategory === d
                ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground hover:translate-x-0.5"
            }`}
          >
            <FolderOpen className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">{d}</span>
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="p-4 border-t border-sidebar-border space-y-3">
        <div className="flex items-center gap-2 text-xs text-sidebar-foreground">
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Total Queries</span>
          <span className="ml-auto font-medium text-sidebar-accent-foreground">{totalQueries}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-sidebar-foreground">
          <Activity className="w-3.5 h-3.5" />
          <span>Active Category</span>
          <span className="ml-auto font-medium text-sidebar-accent-foreground truncate max-w-[80px]">
            {activeCategory ?? "All"}
          </span>
        </div>
      </div>
    </aside>
  </>
);

export default KnowledgeSidebar;
