import { Menu } from "lucide-react";

interface AppHeaderProps {
  onToggleSidebar: () => void;
}

const AppHeader = ({ onToggleSidebar }: AppHeaderProps) => (
  <header className="h-14 border-b border-border bg-card/80 backdrop-blur-sm flex items-center justify-between px-4 flex-shrink-0">
    <div className="flex items-center gap-3">
      <button
        onClick={onToggleSidebar}
        className="w-8 h-8 rounded-lg hover:bg-secondary flex items-center justify-center transition-colors lg:hidden"
      >
        <Menu className="w-4 h-4 text-muted-foreground" />
      </button>
      <h1 className="text-sm font-semibold text-foreground">AI Knowledge Assistant</h1>
    </div>
    <div className="flex items-center gap-4 text-xs text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-status-online" />
        System Online
      </span>
      <span className="flex items-center gap-1.5">
        <span className="text-status-fast">⚡</span>
        Fast Mode
      </span>
    </div>
  </header>
);

export default AppHeader;
