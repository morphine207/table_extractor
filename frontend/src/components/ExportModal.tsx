import { useState } from "react";
import { Download, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  totalRows: number;
  lowConfidenceCount: number;
  onExport: (includeConfidence: boolean) => void;
}

const ExportModal = ({ isOpen, onClose, totalRows, lowConfidenceCount, onExport }: ExportModalProps) => {
  const [includeConfidence, setIncludeConfidence] = useState(true);

  const handleExport = () => {
    onExport(includeConfidence);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-lg font-medium">Export to Excel</DialogTitle>
        </DialogHeader>
        
        <div className="py-4">
          <div className="space-y-3 mb-6">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Total rows extracted</span>
              <span className="font-medium text-foreground">{totalRows}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Low confidence rows</span>
              <span className="font-medium text-foreground">{lowConfidenceCount}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
            <Checkbox
              id="include-confidence"
              checked={includeConfidence}
              onCheckedChange={(checked) => setIncludeConfidence(checked as boolean)}
            />
            <label htmlFor="include-confidence" className="text-sm text-foreground cursor-pointer">
              Include confidence column
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleExport} className="gap-2">
            <Download className="w-4 h-4" />
            Download Excel (.xlsx)
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ExportModal;
