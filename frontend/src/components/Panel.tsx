import type { ReactNode } from 'react';

interface PanelProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, children, className = '' }: PanelProps) {
  return (
    <section className={`panel ${className}`.trim()}>
      {title && <div className="panel-title">{title}</div>}
      <div className="panel-body">{children}</div>
    </section>
  );
}
