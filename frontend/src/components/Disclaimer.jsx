import { Scale } from 'lucide-react'
import './Disclaimer.css'

// Cuerpo del aviso legal, compartido por ambas variantes.
function DisclaimerBody() {
  return (
    <div className="disclaimer__body">
      <p className="disclaimer__lead">
        El análisis y la información que ofrece esta aplicación se generan de forma
        automática mediante inteligencia artificial y tienen carácter exclusivamente
        informativo y orientativo.
      </p>
      <ul className="disclaimer__list">
        <li>
          <strong>No constituye asesoramiento legal.</strong> El contenido no representa
          una opinión jurídica ni asesoramiento profesional de ningún tipo, ni reemplaza
          la consulta con un abogado o abogada matriculado/a.
        </li>
        <li>
          <strong>No genera relación profesional.</strong> El uso de esta herramienta no
          crea una relación profesional-cliente ni vínculo de confidencialidad alguno.
        </li>
        <li>
          <strong>Puede contener errores.</strong> Los resultados pueden incluir
          imprecisiones, omisiones o interpretaciones incorrectas, y basarse en normativa
          que no se encuentre actualizada o vigente.
        </li>
        <li>
          <strong>La decisión es suya.</strong> Antes de tomar cualquier decisión o firmar
          un documento, consulte a un profesional del derecho y verifique la normativa
          aplicable en su jurisdicción.
        </li>
      </ul>
      <p className="disclaimer__foot">
        Utilice esta herramienta únicamente como referencia rápida y punto de partida,
        nunca como fuente única para decisiones legales. Los autores no asumen
        responsabilidad por daños o perjuicios derivados del uso de la información aquí
        proporcionada.
      </p>
    </div>
  )
}

export default function Disclaimer({ compact = false }) {
  if (compact) {
    return (
      <details className="disclaimer disclaimer--compact">
        <summary className="disclaimer__summary">
          <Scale size={13} strokeWidth={1.5} />
          <span>
            Aviso legal — análisis orientativo generado por IA, no constituye asesoramiento
            legal.
          </span>
        </summary>
        <DisclaimerBody />
      </details>
    )
  }

  return (
    <aside className="disclaimer disclaimer--full" aria-label="Aviso legal">
      <div className="disclaimer__head">
        <Scale size={15} strokeWidth={1.5} />
        <span>Aviso legal</span>
      </div>
      <DisclaimerBody />
    </aside>
  )
}
