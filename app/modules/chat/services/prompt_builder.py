from backend.app.modules.documents.prompts.sensitivity_prompt import (

    IT_SENSITIVITY_PROMPT,

    HR_SENSITIVITY_PROMPT,

    SALES_SENSITIVITY_PROMPT,

    MARKETING_SENSITIVITY_PROMPT,


)


class PromptBuilder:


    @staticmethod
    def build_sensitivity_prompt(

        content: str,

        department:
        str | None,

        security_level:
        str | None

    ):


        mapping = {

            "IT":

            IT_SENSITIVITY_PROMPT,


            "HR":

            HR_SENSITIVITY_PROMPT,


            "SALES":

            SALES_SENSITIVITY_PROMPT,


            "MARKETING":

            MARKETING_SENSITIVITY_PROMPT,


        }


        prompt = (

            mapping.get(

               
                    department,
              


                HR_SENSITIVITY_PROMPT

            )

        )
        
        
        #print("in ra prompt", prompt)


        return (

            prompt

            .format(

                content=
                content,


                security_level=
                security_level

            )

        )