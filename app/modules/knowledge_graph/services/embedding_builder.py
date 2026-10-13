class EmbeddingBuilder:

    @staticmethod
    def build_entity_text(

        name: str,

        type: str,

        description: str

    ):

        return f"""
Entity: {name}

Type: {type}

Description:
{description}
"""

    @staticmethod
    def build_relationship_text(

        source_name: str,

        target_name: str,

        description: str

    ):

        return f"""
Source:
{source_name}

Target:
{target_name}

Relationship:
{description}
"""