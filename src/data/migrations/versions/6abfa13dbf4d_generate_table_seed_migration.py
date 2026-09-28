"""Generate table seed migration

Revision ID: 6abfa13dbf4d
Revises: 8d1c6c10c941
Create Date: 2026-05-05 01:09:58.503867

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6abfa13dbf4d"
down_revision: Union[str, Sequence[str], None] = "8d1c6c10c941"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ========== user_sex_type ==========
    op.bulk_insert(
        sa.table('user_sex_type', sa.column('id', sa.Integer), sa.column('description', sa.String)),
        [{'id': 1, 'description': 'Feminino'}, {'id': 2, 'description': 'Masculino'}]
    )

    # ========== user_gender_type ==========
    op.bulk_insert(
        sa.table('user_gender_type', sa.column('id', sa.Integer), sa.column('description', sa.String)),
        [{'id': 1, 'description': 'Mulher'}, {'id': 2, 'description': 'Homem'}, {'id': 3, 'description': 'Não-binário'}, {'id': 4, 'description': 'Outro'}, {'id': 5, 'description': 'Prefiro não informar'}]
    )

    # ========== document_type ==========
    op.bulk_insert(
        sa.table('document_type', sa.column('id', sa.Integer), sa.column('description', sa.String)),
        [
            {'id': 1, 'description': 'CPF'},
            {'id': 2, 'description': 'RG'},
            {'id': 3, 'description': 'CIN'},
            {'id': 4, 'description': 'Foto de perfil'},
            {'id': 5, 'description': 'Autorização de matrícula de menor de idade'},
            {'id': 6, 'description': 'Atestado de saúde'},
            {'id': 7, 'description': 'Justificativa de falta'},
            {'id': 8, 'description': 'Carteirinha'},
            {'id': 9, 'description': 'Template ficha de cadastro'},
            {'id': 10, 'description': 'Template atestado de saúde'},
            {'id': 11, 'description': 'Template lista de presença'}
        ]
    )

    # ========== legal_representative_degree ==========
    op.bulk_insert(
        sa.table('legal_representative_degree', sa.column('id', sa.Integer), sa.column('description', sa.String)),
        [
            {'id': 1, 'description': 'Mãe'}, {'id': 2, 'description': 'Pai'}, {'id': 3, 'description': 'Tia'},
            {'id': 4, 'description': 'Tio'}, {'id': 5, 'description': 'Avó'}, {'id': 6, 'description': 'Avô'},
            {'id': 7, 'description': 'Outro'}
        ]
    )

    # ========== user_type ==========
    op.bulk_insert(
        sa.table('user_type',
            sa.column('id', sa.Integer), sa.column('description', sa.String),
            sa.column('register_user', sa.Boolean), sa.column('validate_user_documents', sa.Boolean),
            sa.column('list_secretaries', sa.Boolean), sa.column('list_educators', sa.Boolean),
            sa.column('list_students', sa.Boolean), sa.column('send_broadcast_message', sa.Boolean),
            sa.column('add_courses', sa.Boolean), sa.column('add_classes', sa.Boolean),
            sa.column('emit_user_documents', sa.Boolean)
        ),
        [
            {'id': 1, 'description': 'Administrador', 'register_user': 1, 'validate_user_documents': 1, 'list_secretaries': 1, 'list_educators': 1, 'list_students': 1, 'send_broadcast_message': 1, 'add_courses': 1, 'add_classes': 1, 'emit_user_documents': 0, 'register_educational_unit': 1},
            {'id': 2, 'description': 'Secretário', 'register_user': 1, 'validate_user_documents': 1, 'list_secretaries': 1, 'list_educators': 1, 'list_students': 1, 'send_broadcast_message': 1, 'add_courses': 0, 'add_classes': 0, 'emit_user_documents': 1, 'register_educational_unit': 0},
            {'id': 3, 'description': 'Coordenador', 'register_user': 0, 'validate_user_documents': 0, 'list_secretaries': 0, 'list_educators': 0, 'list_students': 1, 'send_broadcast_message': 0, 'add_courses': 1, 'add_classes': 1, 'emit_user_documents': 1, 'register_educational_unit': 0},
            {'id': 4, 'description': 'Educador', 'register_user': 0, 'validate_user_documents': 0, 'list_secretaries': 0, 'list_educators': 0, 'list_students': 1, 'send_broadcast_message': 0, 'add_courses': 1, 'add_classes': 1, 'emit_user_documents': 0, 'register_educational_unit': 0},
            {'id': 5, 'description': 'Estudante', 'register_user': 0, 'validate_user_documents': 0, 'list_secretaries': 0, 'list_educators': 0, 'list_students': 0, 'send_broadcast_message': 0, 'add_courses': 0, 'add_classes': 0, 'emit_user_documents': 1, 'register_educational_unit': 0},
            {'id': 6, 'description': 'Gestor', 'register_user': 1, 'validate_user_documents': 1, 'list_secretaries': 1, 'list_educators': 1, 'list_students': 1, 'send_broadcast_message': 1, 'add_courses': 1, 'add_classes': 1, 'emit_user_documents': 0, 'register_educational_unit': 0}
        ]
    )

    # ========== document_validation_status_type ==========
    op.bulk_insert(
        sa.table('document_validation_status_type', sa.column('id', sa.Integer), sa.column('description', sa.String)),
        [{'id': 1, 'description': 'Em análise'}, {'id': 2, 'description': 'Aprovado'}, {'id': 3, 'description': 'Rejeitado'}]
    )

    # ========== shift_type ==========
    op.bulk_insert(
        sa.table('shift_type', sa.column('id', sa.Integer), sa.column('description', sa.String)),
        [{'id': 1, 'description': 'Manhã'}, {'id': 2, 'description': 'Tarde'}, {'id': 3, 'description': 'Noite'}]
    )

    # ========== report_type ==========
    op.bulk_insert(
        sa.table('report_type', sa.column('id', sa.Integer), sa.column('description', sa.String)),
        [{'id': 1, 'description': 'Alunos matriculados por curso'}, {'id': 2, 'description': 'Vagas por curso'}]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DELETE FROM report_type WHERE id IN (1, 2)')
    op.execute('DELETE FROM shift_type WHERE id IN (1, 2, 3)')
    op.execute('DELETE FROM document_validation_status_type WHERE id IN (1, 2, 3)')
    op.execute('DELETE FROM user_type WHERE id IN (1, 2, 3, 4, 5)')
    op.execute('DELETE FROM legal_representative_degree WHERE id IN (1, 2, 3, 4, 5, 6, 7)')
    op.execute('DELETE FROM document_type WHERE id IN (1, 2, 3, 4, 5, 6, 7)')
    op.execute('DELETE FROM user_gender_type WHERE id IN (1, 2, 3, 4)')
    op.execute('DELETE FROM user_sex_type WHERE id IN (1, 2)')
