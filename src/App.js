import { Provider } from "react-redux";
import store from "./store";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom"

import Home from "./containers/Home";
import Error404 from "./containers/errors/Error404";

import Signup from "./containers/auth/Signup";
import Activate from "./containers/auth/Activate";
import Login from "./containers/auth/Login";

function App() {
  return (
    <Provider store={store}>
      <Router>
        <Routes>
          {/* Error Display */}
          <Route path='*' element={<Error404/>}/>

          <Route exact path='/' element={<Home/>}/>

          {/* Auth */}
          <Route exact path='/signup' element={<Signup/>}/>
          <Route exact path='/login' element={<Login/>}/>
          <Route exact path='/activate/:uid/:token' element={<Activate/>}/>


        </Routes>
      </Router>
    </Provider>
  );
}

export default App;
