import type { PaginatedResponse } from "../types";

type Props<T> = {
  data: PaginatedResponse<T> | null;
  onPageChange: (page: number) => void;
};

export function Pagination<T>({ data, onPageChange }: Props<T>) {
  if (!data || data.pages <= 1) return null;

  return (
    <div className="pagination">
      <button
        className="secondary-button"
        disabled={data.page <= 1}
        onClick={() => onPageChange(data.page - 1)}
      >
        ← Назад
      </button>
      <span>
        Страница <strong>{data.page}</strong> из <strong>{data.pages}</strong> · всего {data.total}
      </span>
      <button
        className="secondary-button"
        disabled={data.page >= data.pages}
        onClick={() => onPageChange(data.page + 1)}
      >
        Вперед →
      </button>
    </div>
  );
}
