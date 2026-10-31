interface StatusMessageProps {
  message: string;
  tone?: 'success' | 'error' | 'warning' | 'info';
  label?: string;
}

export default function StatusMessage({
  message,
  tone = 'info',
  label,
}: StatusMessageProps) {
  const icon = tone === 'success' ? '✓' : tone === 'info' ? 'i' : '!';
  return (
    <p
      className={`status-message status-message--${tone}`}
      role={tone === 'error' || tone === 'warning' ? 'alert' : 'status'}
      aria-label={label}
    >
      <span className="status-message__icon" aria-hidden="true">
        {icon}
      </span>
      {message}
    </p>
  );
}
