export default function AnswerCard({ answer }) {
  if (!answer) return null;

  const isWarning = answer.startsWith("⚠");

  return (
    <div className={`answer-card ${isWarning ? "answer-warning" : ""}`}>
      <div className="answer-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
          <path d="M16 14H8a4 4 0 0 0-4 4v2h16v-2a4 4 0 0 0-4-4z" />
        </svg>
        <span>AI Answer</span>
      </div>
      <div className="answer-body">{answer}</div>
    </div>
  );
}
