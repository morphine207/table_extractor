import { useState } from "react";
import { Download, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ExtractedRow, FilterOption } from "@/types/extraction";
import ConfidenceDot from "./ConfidenceDot";

interface ExtractedTableProps {
  header: string[];
  rows: ExtractedRow[];
  selectedRow: ExtractedRow | null;
  onRowSelect: (row: ExtractedRow) => void;
  onExportClick: () => void;
}

const ExtractedTable = ({ header, rows, selectedRow, onRowSelect, onExportClick }: ExtractedTableProps) => {
  const [filter, setFilter] = useState<FilterOption>('all');

  const filteredRows = filter === 'low-confidence' 
    ? rows.filter(row => row.confidence < 0.8)
    : rows;

  return (
    <div className="h-full flex flex-col bg-card border-l border-border">
      {/* Header */}
      <div className="h-12 px-4 flex items-center justify-between border-b border-border">
        <h2 className="font-medium text-foreground">Extracted Results</h2>
        
        <div className="flex items-center gap-2">
          <Select value={filter} onValueChange={(v) => setFilter(v as FilterOption)}>
            <SelectTrigger className="w-[160px] h-8 text-sm">
              <Filter className="w-3.5 h-3.5 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All rows</SelectItem>
              <SelectItem value="low-confidence">Low confidence only</SelectItem>
            </SelectContent>
          </Select>
          
          <Button size="sm" onClick={onExportClick} className="h-8">
            <Download className="w-4 h-4 mr-2" />
            Export to Excel
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-card z-10">
            <tr className="border-b border-border">
              {header.map((h, i) => (
                <th
                  key={`${h}-${i}`}
                  className="text-left font-medium text-muted-foreground px-3 py-2.5 whitespace-nowrap"
                >
                  {h || `Column ${i + 1}`}
                </th>
              ))}
              <th className="text-center font-medium text-muted-foreground px-3 py-2.5 w-16">Conf.</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, index) => (
              <tr
                key={row.id}
                onClick={() => onRowSelect(row)}
                className={`cursor-pointer transition-colors table-row-hover ${
                  selectedRow?.id === row.id ? 'table-row-selected' : index % 2 === 1 ? 'table-row-alt' : ''
                }`}
              >
                {header.map((_h, i) => (
                  <td key={`${row.id}-${i}`} className="px-3 py-2.5 text-foreground whitespace-nowrap">
                    {row.values[i] ?? ""}
                  </td>
                ))}
                <td className="px-3 py-2.5 text-center">
                  <ConfidenceDot confidence={row.confidence} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer summary */}
      <div className="h-10 px-4 flex items-center justify-between border-t border-border text-xs text-muted-foreground">
        <span>{filteredRows.length} rows</span>
        <span>{rows.filter(r => r.confidence < 0.8).length} low confidence</span>
      </div>
    </div>
  );
};

export default ExtractedTable;
