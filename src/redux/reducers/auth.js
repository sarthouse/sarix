import {
    SIGNUP_SUCCESS,
    SIGNUP_FAIL,
} from '../actions/types'

const initialState = {
    access: localStorage.getItem('access'),
    refresh: localStorage.getItem('refresh'),
    isAuthenticated: null,
    user: null,
    loading: false
}

export default function Auth(state = initialState, action) {
    const {type, payload} = action;

    switch(type){
        case SIGNUP_SUCCESS:
        case SIGNUP_FAIL:
            localStorage.setItem('access')
            localStorage.setItem('refresh')
            return {
                ...state,
                access:null,
                refresh:null,
                isAuthenticated: false,
                user: null,
            }
        
        default:
            return state
    }
}