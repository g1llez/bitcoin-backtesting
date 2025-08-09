from sqlalchemy import text
from sqlalchemy.engine import Engine
import logging


logger = logging.getLogger(__name__)


def run_startup_migrations(engine: Engine) -> None:
    """
    Execute minimal, idempotent startup migrations until full Alembic is wired.
    - Ensure unique constraint on site_machine_instances (site_id, template_id)
    """
    with engine.begin() as conn:
        # Vérifier s'il existe des doublons qui empêcheraient la contrainte UNIQUE
        duplicates = conn.execute(
            text(
                """
                SELECT site_id, template_id, COUNT(*) AS c
                FROM site_machine_instances
                GROUP BY site_id, template_id
                HAVING COUNT(*) > 1
                """
            )
        ).fetchall()

        if duplicates:
            # Ne pas appliquer la contrainte si des doublons existent; journaliser
            logger.warning(
                "Contraintes UNIQUE (site_id, template_id) non appliquées: doublons existants: %s",
                [(row[0], row[1], row[2]) for row in duplicates],
            )
        else:
            # Ajouter la contrainte si elle n'existe pas déjà
            conn.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'uq_site_machine_instance_site_template'
                        ) THEN
                            ALTER TABLE IF EXISTS site_machine_instances
                            ADD CONSTRAINT uq_site_machine_instance_site_template
                            UNIQUE (site_id, template_id);
                        END IF;
                    END
                    $$;
                    """
                )
            )


