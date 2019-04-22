import jwtDecode from 'jwt-decode';
import * as auth from '../actions/authActions';

const initialState = {
    access: undefined,
    refresh: undefined,
    userDetails: {},
    errors: {}
}

export default (state = initialState, action) => {
    switch (action.type) {
        case auth.LOGIN_SUCCESS:
            return {
                access: {
                    token: action.payload.access,
                    ...jwtDecode(action.payload.access)
                },
                refresh: {
                    token: action.payload.refresh,
                    ...jwtDecode(action.payload.refresh)
                },
                userDetails: {
                    user_id: jwtDecode(action.payload.access).user_id,
                    username: jwtDecode(action.payload.access).username
                },
                errors: {}
            }
        case auth.TOKEN_RECEIVED:
            return {
                ...state,
                access: {
                    token: action.payload.access,
                    ...jwtDecode(action.payload.access)
                }
            }
        case auth.LOGIN_FAILURE:
        case auth.TOKEN_FAILURE:
            return {
                access: undefined,
                refresh: undefined,
                userDetails: undefined,
                errors: action.payload.response || { 'non_field_errors': action.payload.statusText }
            }
        case auth.LOGOUT_REQUEST:
            return {
                access: undefined,
                refresh: undefined,
                userDetails: undefined,
                errors: {}
            }
        default:
            return state
    }
}

export function accessToken(state) {
    if (state.access) {
        return state.access.token
    }
}

export function refreshToken(state) {
    if (state.refresh) {
        return state.refresh.token
    }
}

export function isAccessTokenExpired(state) {
    if (state.access && state.access.exp) {
        return 1000 * state.access.exp - (new Date().getTime()) < 5000
    }
    return true;
}

export function isRefreshTokenExpired(state) {
    if (state.refresh && state.refresh.exp) {
        return 1000 * state.refresh.exp - (new Date().getTime()) < 5000
    }
    return true;
}

export function isAuthenticated(state) {
    return !isRefreshTokenExpired(state)
}

export function errors(state) {
    return state.errors
}

export function userID(state) {
    if (state.access) {
        return state.access.user_id
    }
}

export function fullName(state) {
    if (state.access) {
        return state.access.user_claims.user_details.name
    }
}