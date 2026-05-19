type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="pagination">
      <span>
        Показано {from}–{to} из {total}
      </span>
      <div className="pagination-buttons">
        <button className="secondary-button" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Назад
        </button>
        <strong>
          {page} / {totalPages}
        </strong>
        <button className="secondary-button" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
          Вперёд
        </button>
      </div>
    </div>
  );
}
