import { FileText } from "lucide-react";

interface HeaderProps {
  showLogo?: boolean;
}

const Header = ({ showLogo = true }: HeaderProps) => {
  return (
    <header className="h-14 border-b border-border bg-card px-6 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <FileText className="w-5 h-5 text-primary" />
        <span className="font-semibold text-foreground">Table Extractor</span>
        <span className="text-xs text-muted-foreground ml-1">for Legal</span>
      </div>
      {showLogo && (
        <img
          src="/logo.png"
          alt="Firm logo"
          className="h-8 w-auto object-contain"
        />
      )}
    </header>
  );
};

export default Header;
