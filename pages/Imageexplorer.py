import pandas as pd
import pvision
from streamlit_image_select import image_select
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import helper

st.session_state.render_image = False


def filter_view():
    """
    This function displays the filter view page.

    The filter view page allows users to filter their currently active images without changing the view. Users can move, copy, and delete the selected images.

    def filter_view():
        """
        This function displays the filter view page.
    
        The filter view page allows users to filter their currently active images without changing the view. Users can move, copy, and delete the selected images.
    
        """
        st.subheader("Drill down into your currently active images")
        st.write(
            "This page lets you filter your current images without changing the the view such as filtering in the 'Promptvision' tab. When filtering here you can move, copy and delete the images you have selected."
        )
        # Use the filter_dataframe function on your dataframe
        filtered_df = pvision.filter_dataframe(st.session_state.df)
        # Rest of the code


# Rest of
