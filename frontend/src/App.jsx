import './App.css';
import risci_pic from './assets/RISCI_GradPic (2018).JPG';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={risci_pic} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
